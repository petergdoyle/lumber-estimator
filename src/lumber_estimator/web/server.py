import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

from src.lumber_estimator.core.config import load_project_config
from src.lumber_estimator.core.estimator import run_estimation

app = FastAPI(title="Lumber Estimator API")

# Mount early so it doesn't interfere with API routes
# We will create the 'web' directory at the root
if os.path.exists("web"):
    app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")

class ProjectInfo(BaseModel):
    id: str
    name: str
    path: str

@app.get("/api/projects", response_model=List[ProjectInfo])
def list_projects():
    projects_dir = "projects"
    projects = []
    if not os.path.exists(projects_dir):
        return []
    
    for d in os.listdir(projects_dir):
        p_path = os.path.join(projects_dir, d)
        if os.path.isdir(p_path) and os.path.exists(os.path.join(p_path, "project.yaml")):
            try:
                config = load_project_config(d, base_dir=projects_dir)
                projects.append(ProjectInfo(
                    id=d,
                    name=config.get('name', d),
                    path=p_path
                ))
            except:
                continue
    return projects

@app.get("/api/projects/{project_id}")
def get_project_details(project_id: str):
    try:
        config = load_project_config(project_id, base_dir="projects")
        return config
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/projects/{project_id}/estimate")
def estimate_project(project_id: str):
    try:
        config = load_project_config(project_id, base_dir="projects")
        summary_df = run_estimation(config)
        return summary_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Lumber Estimator API is running. Visit /ui for the interface."}

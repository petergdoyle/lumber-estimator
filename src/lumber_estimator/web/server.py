import os
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import shutil
import csv
import yaml
import re

from src.lumber_estimator.core.config import load_project_config
from src.lumber_estimator.core.estimator import run_estimation
from src.lumber_estimator.core.visualize import generate_volume_chart, compile_report_pdf, generate_buy_report_pdf

app = FastAPI(title="Lumber Estimator API")

def kebab_case(string):
    string = string.lower()
    string = re.sub(r'[\s_]+', '-', string)
    string = re.sub(r'[^a-z0-9\-]', '', string)
    return string.strip('-')

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
        
        # Trigger visualization generation
        project_dir = os.path.join("projects", project_id)
        generate_volume_chart(summary_df, project_dir)
        compile_report_pdf(project_dir)
        generate_buy_report_pdf(project_dir)
        
        return summary_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/download/{report_type}")
def download_report(project_id: str, report_type: str):
    base_dir = "projects"
    project_dir = os.path.join(base_dir, project_id)
    
    mapping = {
        "color": "visual_report.pdf",
        "grayscale": "visual_report_grayscale.pdf",
        "buy": "buy_report.pdf"
    }
    
    if report_type not in mapping:
        raise HTTPException(status_code=400, detail="Invalid report type. Use 'color', 'grayscale', or 'buy'.")
    
    file_path = os.path.join(project_dir, mapping[report_type])
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Report file not found: {mapping[report_type]}")
        
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=mapping[report_type]
    )


@app.post("/api/projects")
async def create_project(
    name: str = Form(...),
    waste_lumber: float = Form(0.30),
    waste_sheet: float = Form(0.20),
    cut_spacing: float = Form(0.125),
    rotatable_materials: str = Form("MDF, Melamine, OSB"),
    parts_file: Optional[UploadFile] = File(None),
    inventory_file: Optional[UploadFile] = File(None)
):
    try:
        folder_name = kebab_case(name)
        project_dir = os.path.join("projects", folder_name)
        
        if os.path.exists(project_dir):
            raise HTTPException(status_code=400, detail=f"Project folder '{folder_name}' already exists.")
            
        os.makedirs(project_dir, exist_ok=True)
        
        # Parse rotatables
        rotatables = [m.strip() for m in rotatable_materials.split(',')]
        
        # Generate project.yaml
        yaml_config = {
            'project': {
                'name': name,
                'files': {
                    'parts': 'parts.csv',
                    'inventory': 'on-hand.csv'
                },
                'waste_allowances': {
                    'lumber': float(waste_lumber),
                    'sheet_goods': float(waste_sheet),
                    'cut_spacing': float(cut_spacing)
                },
                'rotatable_materials': rotatables
            }
        }
        
        yaml_path = os.path.join(project_dir, 'project.yaml')
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_config, f, sort_keys=False)
            
        # Handle Parts CSV
        parts_path = os.path.join(project_dir, 'parts.csv')
        if parts_file and parts_file.filename:
            with open(parts_path, 'wb') as f:
                shutil.copyfileobj(parts_file.file, f)
        else:
            with open(parts_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Description', 'Length', 'Width', 'Quantity', 'Material Type', 'Material'])
                
        # Handle Inventory CSV
        inventory_path = os.path.join(project_dir, 'on-hand.csv')
        if inventory_file and inventory_file.filename:
            with open(inventory_path, 'wb') as f:
                shutil.copyfileobj(inventory_file.file, f)
        else:
            with open(inventory_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Label', 'Length', 'Width', 'Quantity', 'Material Type', 'Material'])
                
        return {"status": "success", "project_id": folder_name}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Lumber Estimator API is running. Visit /ui for the interface."}

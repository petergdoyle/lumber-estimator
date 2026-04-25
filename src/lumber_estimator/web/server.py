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
import tarfile
from datetime import datetime

from src.lumber_estimator.core.config import load_project_config
from src.lumber_estimator.core.estimator import run_estimation
from src.lumber_estimator.core.visualize import generate_volume_chart, compile_report_pdf, generate_buy_report_pdf, generate_inventory_report_pdf, generate_verification_report_pdf, generate_master_report_pdf

app = FastAPI(title="Lumber Estimator API")

def kebab_case(string):
    string = string.lower()
    string = re.sub(r'[\s_]+', '-', string)
    string = re.sub(r'[^a-z0-9\-]', '', string)
    return string.strip('-')
    
def validate_csv_headers(file: UploadFile, expected_headers: List[str]):
    """
    Validates that the upload has the correct headers and all rows have the same column count.
    """
    try:
        # Read the file content
        content = file.file.read().decode('utf-8').splitlines()
        file.file.seek(0) # Reset file pointer for later reading/saving
        
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        reader = csv.reader(content)
        headers = next(reader, None)
        
        if not headers:
            raise HTTPException(status_code=400, detail="Uploaded file has no headers.")
            
        # Clean headers
        headers = [h.strip() for h in headers]
        expected_headers = [h.strip() for h in expected_headers]
        
        if headers != expected_headers:
            raise HTTPException(status_code=400, detail=f"Invalid CSV headers. Expected: {', '.join(expected_headers)}")
            
        # Validate row alignment
        expected_col_count = len(expected_headers)
        for i, row in enumerate(reader, start=2):
            if len(row) != expected_col_count:
                raise HTTPException(status_code=400, detail=f"Row {i} in CSV has mismatched column count. Expected {expected_col_count}, got {len(row)}.")
                
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a standard UTF-8 CSV.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"CSV validation error: {str(e)}")

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

@app.post("/api/projects/{project_id}/archive")
def archive_project(project_id: str):
    base_dir = "projects"
    archive_dir = "archives"
    project_path = os.path.join(base_dir, project_id)
    
    if not os.path.exists(project_path):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
        
    try:
        # Ensure archives directory exists
        os.makedirs(archive_dir, exist_ok=True)
        
        # Generate archive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_filename = f"{project_id}_{timestamp}.tar.bz2"
        archive_path = os.path.join(archive_dir, archive_filename)
        
        # Create tar.bz2 archive
        with tarfile.open(archive_path, "w:bz2") as tar:
            tar.add(project_path, arcname=project_id)
            
        # Verify archive was created before deleting original
        if os.path.exists(archive_path):
            shutil.rmtree(project_path)
        else:
            raise Exception("Failed to create archive file.")
            
        return {"status": "success", "message": f"Project '{project_id}' archived as {archive_filename}"}
    except Exception as e:
        # Cleanup partial archive if it exists
        if 'archive_path' in locals() and os.path.exists(archive_path):
            os.remove(archive_path)
        raise HTTPException(status_code=500, detail=f"Archival failed: {str(e)}")

@app.get("/api/projects/{project_id}/estimation")
def get_project_estimation(project_id: str):
    project_dir = os.path.join("projects", project_id)
    summary_path = os.path.join(project_dir, 'estimation_summary.csv')
    
    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="Estimation results not found.")
        
    try:
        results = []
        with open(summary_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings to float where possible for cleaner UI rendering
                processed_row = {}
                for k, v in row.items():
                    try:
                        processed_row[k] = float(v) if '.' in v or v.isdigit() else v
                    except:
                        processed_row[k] = v
                results.append(processed_row)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read estimation results: {str(e)}")

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
        generate_inventory_report_pdf(project_dir)
        generate_verification_report_pdf(project_dir)
        generate_master_report_pdf(project_dir)
        
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
        "buy": "buy_report.pdf",
        "buy_md": "buy_report.md",
        "inventory": "inventory_utilization.pdf",
        "inventory_md": "inventory_utilization.md",
        "verification": "data_verification.pdf",
        "verification_md": "data_verification.md",
        "master": "master_report.pdf",
        "master_md": "master_report.md"
    }
    
    if report_type not in mapping:
        allowed = ", ".join(mapping.keys())
        raise HTTPException(status_code=400, detail=f"Invalid report type. Supported: {allowed}")
    
    file_path = os.path.join(project_dir, mapping[report_type])
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Report file not found: {mapping[report_type]}")
        
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=mapping[report_type]
    )

@app.post("/api/projects/{project_id}/upload")
async def upload_files(
    project_id: str,
    parts_file: Optional[UploadFile] = File(None),
    inventory_file: Optional[UploadFile] = File(None)
):
    base_dir = "projects"
    project_dir = os.path.join(base_dir, project_id)
    
    if not os.path.exists(project_dir):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
        
    # Get target filenames from project config
    try:
        config = load_project_config(project_id, base_dir=base_dir)
        target_parts = config.get('files', {}).get('parts', 'parts.csv')
        target_inventory = config.get('files', {}).get('inventory', 'inventory.csv')
    except Exception as e:
        # Fallback to defaults if config load fails
        target_parts = 'parts.csv'
        target_inventory = 'inventory.csv'

    # Validate headers if files are provided
    if parts_file and parts_file.filename:
        validate_csv_headers(parts_file, ['Description', 'Length', 'Width', 'Quantity', 'Material Type', 'Material'])
    if inventory_file and inventory_file.filename:
        validate_csv_headers(inventory_file, ['Label', 'Length', 'Width', 'Quantity', 'Material Type', 'Material'])

    try:
        # Handle Parts CSV
        if parts_file and parts_file.filename:
            parts_path = os.path.join(project_dir, target_parts)
            with open(parts_path, 'wb') as f:
                shutil.copyfileobj(parts_file.file, f)
                
        # Handle Inventory CSV
        if inventory_file and inventory_file.filename:
            inventory_path = os.path.join(project_dir, target_inventory)
            with open(inventory_path, 'wb') as f:
                shutil.copyfileobj(inventory_file.file, f)
                
        return {"status": "success", "message": f"Files uploaded successfully ({target_parts}, {target_inventory})."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    # Move validation to the TOP before any side effects
    if parts_file and parts_file.filename:
        validate_csv_headers(parts_file, ['Description', 'Length', 'Width', 'Quantity', 'Material Type', 'Material'])
    if inventory_file and inventory_file.filename:
        validate_csv_headers(inventory_file, ['Label', 'Length', 'Width', 'Quantity', 'Material Type', 'Material'])

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
                    'inventory': 'inventory.csv'
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
        inventory_path = os.path.join(project_dir, 'inventory.csv')
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

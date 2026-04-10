import os
import shutil
from pathlib import Path
import sys

def get_projects(projects_dir="projects"):
    projects = []
    if os.path.exists(projects_dir):
        for p in os.listdir(projects_dir):
            if os.path.isdir(os.path.join(projects_dir, p)) and os.path.exists(os.path.join(projects_dir, p, "project.yaml")):
                projects.append(p)
    return projects

def get_items_to_delete(target_dir):
    files_to_delete = []
    dirs_to_delete = []
    p = Path(target_dir)
    
    # Files
    patterns = ["*.pdf", "*.png", "buy_report.md", "estimation_summary.csv", "purchasing_dimensions.csv"]
    for ext in patterns:
        files_to_delete.extend(list(p.rglob(ext)))
        
    # Directories
    for d in p.rglob("blueprints*"):
        if d.is_dir():
            dirs_to_delete.append(d)
            
    return files_to_delete, dirs_to_delete

def main():
    projects = get_projects()
    if not projects:
        print("No projects found.")
        return

    print("Do you want to clean outputs for [A]ll projects or a [S]pecific project?")
    choice = input("Enter A or S (or anything else to cancel): ").strip().lower()
    
    target_dir = "projects"
    if choice == 's':
        print(f"Available projects: {', '.join(projects)}")
        proj = input("Enter project name: ").strip()
        if proj not in projects:
            print(f"Invalid project '{proj}'. Aborting.")
            return
        target_dir = f"projects/{proj}"
    elif choice == 'a':
        target_dir = "projects"
    else:
        print("Aborted.")
        return

    files_to_delete, dirs_to_delete = get_items_to_delete(target_dir)
    
    if not files_to_delete and not dirs_to_delete:
        print(f"No outputs found to delete in {target_dir}.")
        return

    print(f"\nThe following items will be deleted in {target_dir}:")
    for f in files_to_delete:
        print(f)
    for d in dirs_to_delete:
        print(d)
        
    print()
    confirm_yn = input("Are you sure you want to delete these outputs? [y/N]: ").strip().lower()
    if confirm_yn != 'y':
        print("Aborted. No files were deleted.")
        return
        
    confirm_del = input("Please type DELETE to confirm: ").strip()
    if confirm_del != "DELETE":
        print("Aborted. No files were deleted.")
        return
        
    print("Deleting...")
    for f in files_to_delete:
        try:
            f.unlink()
        except Exception as e:
            print(f"Error deleting {f}: {e}")
            
    for d in dirs_to_delete:
        try:
            shutil.rmtree(d)
        except Exception as e:
            print(f"Error deleting directory {d}: {e}")
            
    print("Done.")

if __name__ == "__main__":
    main()

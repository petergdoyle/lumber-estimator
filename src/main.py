import os
import argparse
import sys
from config import load_project_config
from estimator import run_estimation
from visualize import generate_volume_chart

def main():
    parser = argparse.ArgumentParser(description="Lumber Estimator")
    parser.add_argument("project", nargs="?", default="kates-dresser", help="Project name in the projects directory")
    args = parser.parse_args()

    project_name = args.project
    print(f"Lumber Estimator Initialized for project: {project_name}")
    
    try:
        config = load_project_config(project_name, base_dir="projects")
        print(f"Loaded config for project: {config.get('name', project_name)}")
        
        project_dir = config.get('dir')
        parts_file = config.get('files', {}).get('parts', 'parts.csv')
        inventory_file = config.get('files', {}).get('inventory', 'on-hand.csv')
        
        parts_path = os.path.join(project_dir, parts_file)
        
        if inventory_file:
            inventory_path = os.path.join(project_dir, inventory_file)
        else:
            inventory_path = None
        
        # Verify files
        if not os.path.exists(parts_path) or os.path.getsize(parts_path) == 0:
            print(f"Error: Parts file '{parts_file}' is missing or empty in {project_dir}. Cannot proceed.")
            sys.exit(1)
        else:
            print(f"Verified: Parts file '{parts_file}' found and not empty.")
            
        if inventory_path and (not os.path.exists(inventory_path) or os.path.getsize(inventory_path) == 0):
            print(f"Note: Inventory file '{inventory_file}' is missing or empty. Assuming no inventory on-hand.")
            config['files']['inventory'] = None # Inform estimator to skip
        elif inventory_path:
            print(f"Verified: Inventory file '{inventory_file}' found and not empty.")
            
        summary = run_estimation(config)
        print("\nEstimation Summary:")
        print(summary.to_string(index=False))
        
        # Add Visualization Hook
        generate_volume_chart(summary, project_dir)
        
        # Compile everything into a PDF
        from visualize import compile_report_pdf
        compile_report_pdf(project_dir)
        
        print(f"\nSaved estimation summary to {project_dir}/estimation_summary.csv")
        print(f"Saved capacity chart to {project_dir}/capacity_chart.png")
        print(f"Saved visual report to {project_dir}/visual_report.pdf")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

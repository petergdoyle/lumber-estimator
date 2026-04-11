import os
import re
import yaml
import csv

def kebab_case(string):
    """Convert string to kebab-case for folder names."""
    string = string.lower()
    string = re.sub(r'[\s_]+', '-', string)
    string = re.sub(r'[^a-z0-9\-]', '', string)
    return string.strip('-')

def input_with_default(prompt, default_val):
    resp = input(f"{prompt} [{default_val}]: ").strip()
    return resp if resp else default_val

def main():
    print("="*50)
    print("Lumber Estimator - New Project Wizard")
    print("="*50)
    
    project_name = ""
    while not project_name:
        project_name = input("Enter Project Name: ").strip()
        
    folder_name = kebab_case(project_name)
    project_dir = os.path.join("projects", folder_name)
    
    if os.path.exists(project_dir):
        print(f"\nError: Project folder '{folder_name}' already exists.")
        return
        
    os.makedirs(project_dir)
    print(f"\nCreated project directory: {project_dir}")
    
    print("\n--- Allowances & Configurations ---")
    waste_lumber = input_with_default("Waste Allowance - Lumber (e.g., 0.30 for 30%)", "0.30")
    waste_sheet = input_with_default("Waste Allowance - Sheet Goods (e.g., 0.20 for 20%)", "0.20")
    cut_spacing = input_with_default("Cut Spacing / Blade Kerf in inches", "0.125")
    
    rotatables_input = input_with_default(
        "Grain-less materials (comma-separated)",
        "MDF, Melamine, OSB"
    )
    rotatables = [m.strip() for m in rotatables_input.split(',')]
    
    # Generate Project YAML config
    yaml_config = {
        'project': {
            'name': project_name,
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
    
    print(f"\nCreated configuration: {yaml_path}")
    
    # Initialize Parts CSV
    parts_path = os.path.join(project_dir, 'parts.csv')
    with open(parts_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Description', 'Length', 'Width', 'Quantity', 'Material Type', 'Material'])
        
    # Initialize Inventory CSV
    inventory_path = os.path.join(project_dir, 'inventory.csv')
    with open(inventory_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Label', 'Length', 'Width', 'Quantity', 'Material Type', 'Material'])
        
    print(f"Initialized CSV templates: parts.csv, inventory.csv")
    
    # Interactive Part Addition
    print("\n--- Setup Data ---")
    add_parts = input("Would you like to interactively add some parts now? (y/N): ").strip().lower()
    if add_parts == 'y':
        print("\nEntering interactive mode. Type 'done' or leave Description empty to finish.")
        with open(parts_path, 'a', newline='') as f:
            writer = csv.writer(f)
            while True:
                print("-" * 30)
                desc = input("Description (e.g., Side Panel): ").strip()
                if not desc or desc.lower() == 'done':
                    break
                length = input("Length (in): ").strip()
                width = input("Width (in): ").strip()
                qty = input_with_default("Quantity", "1")
                mat_type = input_with_default("Material Type (Lumber / Sheet Goods)", "Lumber")
                m_name = input("Material Name (e.g., 4/4 Cherry): ").strip()
                
                writer.writerow([desc, length, width, qty, mat_type, m_name])
                print(f"Added {qty}x {desc}.")

    add_inv = input("\nWould you like to interactively add some on-hand inventory now? (y/N): ").strip().lower()
    if add_inv == 'y':
        print("\nEntering interactive mode. Type 'done' or leave Label empty to finish.")
        with open(inventory_path, 'a', newline='') as f:
            writer = csv.writer(f)
            while True:
                print("-" * 30)
                label = input("Label (e.g., Board A): ").strip()
                if not label or label.lower() == 'done':
                    break
                length = input("Length (in): ").strip()
                width = input("Width (in): ").strip()
                qty = input_with_default("Quantity", "1")
                mat_type = input_with_default("Material Type (Lumber / Sheet Goods)", "Lumber")
                m_name = input("Material Name (e.g., 4/4 Cherry): ").strip()
                
                writer.writerow([label, length, width, qty, mat_type, m_name])
                print(f"Added {qty}x {label} to inventory.")

    print("="*50)
    print(f"Success! Project '{project_name}' is ready to go.")
    print(f"You can open '{project_dir}/parts.csv' to enter components.")
    print(f"Run 'make project-{folder_name}' when ready to analyze.")

if __name__ == "__main__":
    main()

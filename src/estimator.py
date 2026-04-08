import pandas as pd
import os
import re
from config import load_project_config
from dimensions import parse_fraction, calculate_bf, calculate_sqft

def extract_thickness(mat):
    mat = str(mat)
    m = re.search(r'(\d+/\d+)', mat)
    if m:
        return m.group(1)
    return "4/4"  # Default to 4/4 if not found

def clean_material_name(mat):
    mat = str(mat).strip()
    mat = mat.replace('"', '')
    return mat

def run_estimation(config):
    project_dir = config['dir']
    parts_file = config.get('files', {}).get('parts', 'parts.csv')
    inventory_file = config.get('files', {}).get('inventory', 'on-hand.csv')
    
    parts_path = os.path.join(project_dir, parts_file)
    if inventory_file:
        inventory_path = os.path.join(project_dir, inventory_file)
    else:
        inventory_path = None
    
    if not os.path.exists(parts_path):
        raise FileNotFoundError(f"Parts file not found: {parts_path}")
        
    parts_df = pd.read_csv(parts_path)
    parts_df.columns = [c.strip().lower().replace(' ', '_') for c in parts_df.columns]
    
    # Process required dimensions
    parts_df = parts_df.dropna(subset=['length', 'width', 'material'])
    parts_df['material'] = parts_df['material'].apply(clean_material_name)
    parts_df['length_val'] = parts_df['length'].apply(parse_fraction)
    parts_df['width_val'] = parts_df['width'].apply(parse_fraction)
    parts_df['qty'] = pd.to_numeric(parts_df.get('quantity', 1.0), errors='coerce').fillna(1.0)
    parts_df['thickness'] = parts_df['material'].apply(extract_thickness)
    
    # Calculate Base BF/SQFT
    parts_df['bf'] = parts_df.apply(lambda r: calculate_bf(r['length_val'], r['width_val'], r['thickness']) * r['qty'], axis=1)
    parts_df['sqft'] = parts_df.apply(lambda r: calculate_sqft(r['length_val'], r['width_val']) * r['qty'], axis=1)
    
    # Group totals
    raw_totals = parts_df.groupby(['material_type', 'material'])[['bf', 'sqft']].sum().reset_index()
    
    # Apply Waste Allowances
    waste_lumber = config.get('waste_allowances', {}).get('lumber', 0.30)
    waste_sheet = config.get('waste_allowances', {}).get('sheet_goods', 0.20)
    
    def apply_waste(row):
        is_lumber = 'lumber' in str(row['material_type']).lower()
        val = row['bf'] if is_lumber else row['sqft']
        waste = waste_lumber if is_lumber else waste_sheet
        return val * (1.0 + waste)
        
    raw_totals['total_needed'] = raw_totals.apply(apply_waste, axis=1)
    
    # Process on-hand inventory
    inventory_bf = {}
    inventory_sqft = {}
    if inventory_path and os.path.exists(inventory_path) and os.path.getsize(inventory_path) > 0:
        inv_df = pd.read_csv(inventory_path)
        inv_df.columns = [c.strip().lower().replace(' ', '_') for c in inv_df.columns]
        if not inv_df.empty:
            inv_df = inv_df.dropna(subset=['length', 'width', 'material'])
            inv_df['material'] = inv_df['material'].apply(clean_material_name)
            inv_df['length_val'] = inv_df['length'].apply(parse_fraction)
            inv_df['width_val'] = inv_df['width'].apply(parse_fraction)
            inv_df['qty'] = pd.to_numeric(inv_df.get('quantity', 1.0), errors='coerce').fillna(1.0)
            inv_df['thickness'] = inv_df['material'].apply(extract_thickness)
            
            inv_df['bf'] = inv_df.apply(lambda r: calculate_bf(r['length_val'], r['width_val'], r['thickness']) * r['qty'], axis=1)
            inv_df['sqft'] = inv_df.apply(lambda r: calculate_sqft(r['length_val'], r['width_val']) * r['qty'], axis=1)
            
            inv_totals = inv_df.groupby(['material_type', 'material'])[['bf', 'sqft']].sum().reset_index()
            for _, r in inv_totals.iterrows():
                mat = r['material']
                mtype = r['material_type']
                is_lumber = 'lumber' in str(mtype).lower()
                if is_lumber:
                    inventory_bf[mat] = inventory_bf.get(mat, 0) + r['bf']
                else:
                    inventory_sqft[mat] = inventory_sqft.get(mat, 0) + r['sqft']
                
    # Deduct inventory for final summary
    summary = []
    for _, r in raw_totals.iterrows():
        mat = r['material']
        mtype = r['material_type']
        needed = r['total_needed']
        
        is_lumber = 'lumber' in str(mtype).lower()
        if is_lumber:
            unit = 'BF'
            on_hand = inventory_bf.get(mat, 0.0)
        else:
            unit = 'SQFT'
            on_hand = inventory_sqft.get(mat, 0.0)
            
        to_purchase = max(0.0, needed - on_hand)
        
        summary.append({
            'Material Type': mtype,
            'Material': mat,
            'Raw Need': r['bf'] if is_lumber else r['sqft'],
            'With Waste': needed,
            'On Hand': on_hand,
            'To Purchase': to_purchase,
            'Unit': unit
        })
        
    summary_df = pd.DataFrame(summary)
    
    # Save output to project directory directly
    output_dir = project_dir
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'estimation_summary.csv')
    summary_df.to_csv(out_path, index=False)
    
    return summary_df

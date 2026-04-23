import pandas as pd
import os
import re
from src.lumber_estimator.core.config import load_project_config
from src.lumber_estimator.core.dimensions import parse_fraction, calculate_bf, calculate_sqft
from src.lumber_estimator.core.packer import pack_material
from src.lumber_estimator.core.draw_layout import draw_packed_bin

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
    inventory_file = config.get('files', {}).get('inventory', 'inventory.csv')
    
    parts_path = os.path.join(project_dir, parts_file)
    if inventory_file:
        inventory_path = os.path.join(project_dir, inventory_file)
    else:
        inventory_path = None
    
    if not os.path.exists(parts_path) or os.path.getsize(parts_path) == 0:
        parts_df = pd.DataFrame(columns=['description', 'length', 'width', 'quantity', 'material_type', 'material'])
    else:
        parts_df = pd.read_csv(parts_path)
    
    parts_df.columns = [c.strip().lower().replace(' ', '_') for c in parts_df.columns]
    
    # Process required dimensions
    parts_df = parts_df.dropna(subset=['length', 'width', 'material'])
    if not parts_df.empty:
        parts_df['material'] = parts_df['material'].apply(clean_material_name)
        parts_df['length_val'] = parts_df['length'].apply(parse_fraction)
        parts_df['width_val'] = parts_df['width'].apply(parse_fraction)
        parts_df['qty'] = pd.to_numeric(parts_df.get('quantity', 1.0), errors='coerce').fillna(1.0)
        parts_df['thickness'] = parts_df['material'].apply(extract_thickness)
        
        # Calculate Base BF/SQFT
        parts_df['bf'] = parts_df.apply(lambda r: calculate_bf(r['length_val'], r['width_val'], r['thickness']) * r['qty'], axis=1)
        parts_df['sqft'] = parts_df.apply(lambda r: calculate_sqft(r['length_val'], r['width_val']) * r['qty'], axis=1)
    else:
        parts_df['material'] = pd.Series(dtype=str)
        parts_df['length_val'] = pd.Series(dtype=float)
        parts_df['width_val'] = pd.Series(dtype=float)
        parts_df['qty'] = pd.Series(dtype=float)
        parts_df['thickness'] = pd.Series(dtype=str)
        parts_df['bf'] = pd.Series(dtype=float)
        parts_df['sqft'] = pd.Series(dtype=float)
    
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
            if not inv_df.empty:
                inv_df['material'] = inv_df['material'].apply(clean_material_name)
                inv_df['length_val'] = inv_df['length'].apply(parse_fraction)
                inv_df['width_val'] = inv_df['width'].apply(parse_fraction)
                inv_df['qty'] = pd.to_numeric(inv_df.get('quantity', 1.0), errors='coerce').fillna(1.0)
                inv_df['thickness'] = inv_df['material'].apply(extract_thickness)
                
                inv_df['bf'] = inv_df.apply(lambda r: calculate_bf(r['length_val'], r['width_val'], r['thickness']) * r['qty'], axis=1)
                inv_df['sqft'] = inv_df.apply(lambda r: calculate_sqft(r['length_val'], r['width_val']) * r['qty'], axis=1)
            else:
                inv_df['material'] = pd.Series(dtype=str)
                inv_df['length_val'] = pd.Series(dtype=float)
                inv_df['width_val'] = pd.Series(dtype=float)
                inv_df['qty'] = pd.Series(dtype=float)
                inv_df['thickness'] = pd.Series(dtype=str)
                inv_df['bf'] = pd.Series(dtype=float)
                inv_df['sqft'] = pd.Series(dtype=float)
            
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
    
    # --- 2D BIN PACKING & SHOPPING LIST GENERATION ---
    shopping_list = []
    
    # --- 2D BIN PACKING & SHOPPING LIST GENERATION ---
    shopping_list = []
    
    # Track inventory utilization for report
    inventory_util_data = [] 

    # Process layout algorithm grouping by material
    # Wipe legacy blueprint caches to prevent orphaned ghost files from compiling into the PDF
    import shutil
    blueprints_dir = os.path.join(project_dir, 'blueprints')
    if os.path.exists(blueprints_dir):
        shutil.rmtree(blueprints_dir)

    materials = parts_df['material'].unique()
    for mat in materials:
        # Gather Parts
        m_parts = parts_df[parts_df['material'] == mat]
        parts_list = []
        for i, p in m_parts.iterrows():
            desc = p.get('description', f"Part_{i}")
            if pd.isna(desc):
                desc = f"Part_{i}"
            parts_list.append({
                'id': desc,
                'desc': desc,
                'width': float(p['width_val']),
                'length': float(p['length_val']),
                'qty': int(float(p['qty']))
            })
            
        # Gather Bins (Inventory)
        bins_list = []
        all_bin_ids_for_mat = []
        try:
            if 'inv_df' in locals() and not inv_df.empty:
                m_inv = inv_df[inv_df['material'] == mat]
                for i, b in m_inv.iterrows():
                    lbl = b.get('label', f"Board_{i}")
                    if pd.isna(lbl):
                        lbl = f"Board_{i}"
                    
                    qty = int(float(b['qty']))
                    for q in range(qty):
                        bin_inst_id = f"{lbl}_{q+1}"
                        all_bin_ids_for_mat.append(bin_inst_id)
                    
                    bins_list.append({
                        'id': lbl,
                        'label': lbl,
                        'width': float(b['width_val']),
                        'length': float(b['length_val']),
                        'qty': qty
                    })
        except Exception:
            pass
        
        # Pull cut spacing (kerf) natively from config or default to 0.125
        cut_spacing = config.get('waste_allowances', {}).get('cut_spacing', 0.125)
        
        # Execute Primary Pack extracting the rotation constraint natively from the YAML settings
        rotatable_list = config.get('rotatable_materials', [])
        allow_mat_rotation = any(r_type.lower() in mat.lower() for r_type in rotatable_list)
        
        pack_res = pack_material(parts_list, bins_list, kerf=cut_spacing, allow_rotation=allow_mat_rotation)
        
        # Render Blueprint Visualizations and Track Utilization
        used_bin_ids = set()
        for pbin in pack_res['packed_bins']:
            bin_uid = pbin['bin_uid']
            if "TO_BUY" not in str(bin_uid):
                used_bin_ids.add(bin_uid)
                inventory_util_data.append({
                    'material': mat,
                    'is_used': True,
                    'bin_uid': bin_uid,
                    'width': pbin['width'],
                    'length': pbin['length'],
                    'parts': pbin['rects']
                })
            draw_packed_bin(pbin, mat, project_dir, kerf=cut_spacing)
            
        # Add Unused Bins to report data
        for bin_inst_id in all_bin_ids_for_mat:
            if bin_inst_id not in used_bin_ids:
                # Find the original bin dimensions
                # Note: This is slightly inefficient but safe
                orig_bin = next((b for b in bins_list if b['label'] == bin_inst_id.rsplit('_', 1)[0]), None)
                if orig_bin:
                    inventory_util_data.append({
                        'material': mat,
                        'is_used': False,
                        'bin_uid': bin_inst_id,
                        'width': orig_bin['width'],
                        'length': orig_bin['length'],
                        'parts': []
                    })
            
        # Collect Unpacked orphans for the dimensional shopping list
        # Instead of just dumping them loosely, we pack them into standard "Virtual Boards" for purchasing
        if pack_res['unpacked_parts']:
            is_sheet = "Plywood" in mat or "Sheet Goods" in mat
            virtual_bins = []
            
            remaining_parts = list(pack_res['unpacked_parts'])
            virtual_board_idx = 1
            
            while remaining_parts:
                curr_parts_for_virtual = []
                for up in remaining_parts:
                    curr_parts_for_virtual.append({
                        'id': up['uid'],
                        'desc': up['desc'],
                        'width': up['width'],
                        'length': up['length'],
                        'qty': 1
                    })
                    
                # Virtual Size Heuristics
                if is_sheet:
                    v_width = 48.0
                    v_length = 96.0
                else:
                    v_length = 96.0
                    if curr_parts_for_virtual:
                        # Widest part + kerf + 1 inch padding margin for rough lumber buys
                        v_width = max([p['width'] for p in curr_parts_for_virtual]) + cut_spacing + 1.0 
                    else:
                        v_width = 10.0
                
                v_bin = {
                    'id': f"TO_BUY_{virtual_board_idx}",
                    'label': f"To Buy {mat} Sheet {virtual_board_idx}" if is_sheet else f"To Buy {mat} Board {virtual_board_idx}",
                    'width': v_width,
                    'length': v_length,
                    'qty': 1
                }
                
                # Attempt to pack the leftovers into this single phantom board
                v_pack_res = pack_material(curr_parts_for_virtual, [v_bin], kerf=cut_spacing, allow_rotation=allow_mat_rotation)
                
                packed_pbin = v_pack_res['packed_bins'][0] if v_pack_res['packed_bins'] else None
                if packed_pbin and packed_pbin['rects']:
                    # Draw a native blueprint showing exactly how to break down the new board you buy
                    draw_packed_bin(packed_pbin, mat, project_dir, kerf=cut_spacing)
                    virtual_bins.append({
                        'Material': mat,
                        'Item to Procure': packed_pbin['bin_uid'],
                        'Description': "Virtual Shop Board",
                        'Required Width (in)': v_width,
                        'Required Length (in)': v_length,
                        'parts': packed_pbin['rects']
                    })
                
                # Advance remaining parts loop
                remaining_parts = list(v_pack_res['unpacked_parts'])
                virtual_board_idx += 1
                
                # Absolute safety break against geometry that exceeds 8 feet (like very long rails)
                if virtual_board_idx > 50:
                    for upart in remaining_parts:
                        shopping_list.append({
                            'Material': mat,
                            'Item to Procure': upart['uid'],
                            'Description': "**OVERSIZED PART ERROR**",
                            'Required Width (in)': upart['width'],
                            'Required Length (in)': upart['length'],
                            'parts': []
                        })
                    break
                    
            for vb in virtual_bins:
                shopping_list.append(vb)
            
    # Save the custom shopping list of required material modules
    if shopping_list:
        # Create a copy for CSV export, dropping the complex 'parts' object to keep CSV clean
        csv_shop_list = []
        for s in shopping_list:
            c = s.copy()
            c.pop('parts', None)
            csv_shop_list.append(c)
            
        shop_df = pd.DataFrame(csv_shop_list)
        shop_df.to_csv(os.path.join(project_dir, 'purchasing_dimensions.csv'), index=False)
    else:
        # Write an empty file to indicate perfection
        with open(os.path.join(project_dir, 'purchasing_dimensions.csv'), 'w') as f:
            f.write("Status\nAll parts fit exactly into the on-hand inventory!")
            
    # Save volume output to project directory directly
    output_dir = project_dir
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'estimation_summary.csv')
    summary_df.to_csv(out_path, index=False)
    
    # Generate Unified Buy Report Markdown
    try:
        from src.lumber_estimator.core.dimensions import format_fraction
        report_lines = []
        
        fallback_name = os.path.basename(project_dir.rstrip('/'))
        
        report_lines.append(f"# Shopping List: {config.get('name', fallback_name).title()}")
        report_lines.append(f"> Auto-generated dimensional itemized purchasing guide.\n")
        
        buy_required = False
        # Use full shopping_list list here to access 'parts'
        
        for _, row in summary_df.iterrows():
            mat_name = row['Material']
            needs_volume_buy = row['To Purchase'] > 0.01
            
            # Check if any items in shopping_list match this material
            mat_shop = [s for s in shopping_list if s['Material'] == mat_name]
            needs_physical_buy = len(mat_shop) > 0
            
            if needs_volume_buy or needs_physical_buy:
                buy_required = True
                report_lines.append(f"## {mat_name}")
                
                total_purchase_volume = 0.0
                mapped_boards = []
                
                for s_item in mat_shop:
                    w = s_item['Required Width (in)']
                    l = s_item['Required Length (in)']
                    
                    if row['Material Type'] == 'Sheet Goods':
                        vol = calculate_sqft(l, w)
                    else:
                        vol = calculate_bf(l, w, thickness_moniker=mat_name)
                    
                    total_purchase_volume += vol
                    
                    w_frac = format_fraction(w, max_denominator=32)
                    l_frac = format_fraction(l, max_denominator=32)
                    mapped_boards.append(f"  - [ ] 1x `{w_frac}\" W  x  {l_frac}\" L`  *(Identifier: {s_item['Item to Procure']})*")
                    
                    # Add detailed part breakdown for each board
                    if 'parts' in s_item and s_item['parts']:
                        for p in s_item['parts']:
                            pw_frac = format_fraction(p['width'], max_denominator=32)
                            pl_frac = format_fraction(p['length'], max_denominator=32)
                            mapped_boards.append(f"    - Fulfills: `{p['id']}` (`{pl_frac}\" x {pw_frac}\"`)")
                
                # Derive final quote mapping
                display_volume = total_purchase_volume if total_purchase_volume > 0 else row['To Purchase']
                report_lines.append(f"- **Total Quoted Volume to Buy:** {round(display_volume, 2)} {row['Unit']}")
                
                if mapped_boards:
                    report_lines.append("- **Recommended Boards to Pull:**")
                    report_lines.extend(mapped_boards)
                elif needs_physical_buy:
                    report_lines.append("- *No dimensional layout mapped.*")
                    
                report_lines.append("")
                
        if not buy_required:
            report_lines.append("## Inventory Status: Fully Stocked!")
            report_lines.append("You have sufficient on-hand inventory to cut all parts without purchasing new material.")
            
        with open(os.path.join(project_dir, 'buy_report.md'), 'w') as f:
            f.write("\n".join(report_lines))
    except Exception as e:
        print(f"Warning: Failed to compile Markdown Buy Report - {e}")
    
    # Generate Inventory Utilization Report Markdown
    try:
        from src.lumber_estimator.core.dimensions import format_fraction
        util_lines = []
        util_lines.append(f"# Inventory Utilization Report: {config.get('name', fallback_name).title()}")
        util_lines.append(f"> Detailed breakdown of how current stock is utilized for this project.\n")

        # Group data by material for the report
        mats_with_util = sorted(list(set([d['material'] for d in inventory_util_data])))
        
        for mat in mats_with_util:
            util_lines.append(f"## {mat}")
            
            mat_data = [d for d in inventory_util_data if d['material'] == mat]
            used_data = [d for d in mat_data if d['is_used']]
            unused_data = [d for d in mat_data if not d['is_used']]
            
            # Used Inventory Section
            util_lines.append(f"### Used Inventory Pieces")
            if not used_data:
                util_lines.append("*No on-hand inventory of this material was used.*")
            else:
                for b in used_data:
                    w_frac = format_fraction(b['width'], max_denominator=32)
                    l_frac = format_fraction(b['length'], max_denominator=32)
                    util_lines.append(f"- **{b['bin_uid']}** (`{w_frac}\" x {l_frac}\"`)")
                    for p in b['parts']:
                        # The packer returns 'width' and 'length' of the part rects
                        pw_frac = format_fraction(p['width'], max_denominator=32)
                        pl_frac = format_fraction(p['length'], max_denominator=32)
                        util_lines.append(f"  - Cut: `{p['id']}` (`{pw_frac}\" x {pl_frac}\"`)")
            
            # Unused Inventory Section
            util_lines.append(f"\n### Unused Inventory Pieces")
            if not unused_data:
                util_lines.append("*All on-hand inventory of this material was fully utilized.*")
            else:
                for b in unused_data:
                    w_frac = format_fraction(b['width'], max_denominator=32)
                    l_frac = format_fraction(b['length'], max_denominator=32)
                    util_lines.append(f"- **{b['bin_uid']}** (`{w_frac}\" x {l_frac}\"`)")
            
            util_lines.append("") # Spacer
            
        if not mats_with_util:
            util_lines.append("## No Inventory Data Available")
            util_lines.append("No local inventory was provided or mapped for this project.")

        with open(os.path.join(project_dir, 'inventory_utilization.md'), 'w') as f:
            f.write("\n".join(util_lines))
    except Exception as e:
        print(f"Warning: Failed to compile Markdown Inventory Utilization Report - {e}")

    return summary_df

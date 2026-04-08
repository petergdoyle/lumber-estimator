import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def draw_packed_bin(bin_data, material_name, output_dir):
    """
    Draws a 2D topographical blueprint of a single material board with its packed cuts.
    """
    bin_uid = bin_data['bin_uid']
    bw = bin_data['width']
    bl = bin_data['length']
    rects = bin_data['rects']
    
    if not rects:
        return # Skip empty unutilized bins
        
    # Calculate aspect ratio, capped so incredibly long items don't break matplotlib proportions 
    ratio = bw/bl if bl > 0 else 1
    # Minimum height of 3 for nice rendering
    fig_h = max(3, ratio * 12)
    fig, ax = plt.subplots(figsize=(12, fig_h))
    ax.set_xlim(0, bl)
    ax.set_ylim(0, bw)
    
    # Determine color scheme based on Inventory vs To-Buy
    if "TO_BUY" in str(bin_uid):
        board_edge, board_face = '#6c757d', '#e9ecef' # Cool Grey
        part_edge, part_face = '#5c0f16', '#e76f51' # Terracotta
    else:
        board_edge, board_face = '#5c4033', '#deb887' # Natural Wood
        part_edge, part_face = '#1a1a1a', '#8fbc8f' # Light Green
    
    # Draw Board background
    board = patches.Rectangle((0, 0), bl, bw, linewidth=2, edgecolor=board_edge, facecolor=board_face, alpha=0.5)
    ax.add_patch(board)
    
    # Draw cut parts
    for r in rects:
        # rectpack axes: 'x' binds to width array, 'y' binds to length array
        py = r['x'] 
        px = r['y'] 
        pw = r['width'] 
        pl = r['length'] 
        
        part_patch = patches.Rectangle((px, py), pl, pw, linewidth=1.5, edgecolor=part_edge, facecolor=part_face, alpha=0.9)
        ax.add_patch(part_patch)
        
        # Add bounding label inside
        ax.text(px + pl/2, py + pw/2, r['id'], ha='center', va='center', fontsize=9, color='white', weight='bold')

    plt.title(f"Cut List: {material_name} - Board {bin_uid} ({bw}\" Wide x {bl}\" Long)", fontsize=14, pad=15)
    plt.xlabel("Length Axis (inches)", fontsize=11)
    plt.ylabel("Width Axis (inches)", fontsize=11)
    
    # Normalize filename
    safe_name = material_name.replace('/', '-').replace(' ', '_').replace('"', '')
    safe_bin_id = str(bin_uid).replace('/', '-').replace(' ', '_')
    layout_folder = os.path.join(output_dir, "blueprints")
    os.makedirs(layout_folder, exist_ok=True)
    
    out_file = os.path.join(layout_folder, f"layout_{safe_name}_{safe_bin_id}.png")
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close()

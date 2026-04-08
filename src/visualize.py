import os
import glob
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from PIL import Image

def generate_volume_chart(summary_df, output_dir):
    """
    Generate a bar chart comparing Required volume (With Waste) against On-Hand volume.
    Saves the chart as 'capacity_chart.png' in the given output_dir.
    """
    if summary_df is None or summary_df.empty:
        return
        
    # Set a modern, clean aesthetic
    sns.set_theme(style="whitegrid")
    
    # Setup Figure
    plt.figure(figsize=(10, 6))
    
    # Melt the dataframe to work gracefully with Seaborn's grouped bar charting
    melted = summary_df.melt(
        id_vars=["Material"], 
        value_vars=["With Waste", "On Hand"], 
        var_name="Metric", 
        value_name="Quantity"
    )
                             
    ax = sns.barplot(
        data=melted,
        x="Material",
        y="Quantity",
        hue="Metric",
        palette=["#e63946", "#457b9d"]  # Warm red for requirements, calm blue for stock
    )
    
    plt.title("Materials Required vs. Current Inventory", fontsize=16, pad=15, fontweight='bold')
    plt.ylabel("Quantity (BF or SQFT)", fontsize=12, fontweight='medium')
    plt.xlabel("Material", fontsize=12, fontweight='medium')
    
    # Rotate labels nicely
    plt.xticks(rotation=35, ha='right')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the rendered figure natively
    out_path = os.path.join(output_dir, 'capacity_chart.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

def compile_report_pdf(project_dir):
    """
    Compiles all layout blueprints and the overall capacity chart into a single PDF.
    """
    chart_path = os.path.join(project_dir, 'capacity_chart.png')
    blueprints = glob.glob(os.path.join(project_dir, 'blueprints', '*.png'))
    
    # Sort files conceptually
    blueprints.sort()
    
    images = []
    if os.path.exists(chart_path):
        images.append(chart_path)
    images.extend(blueprints)
    
    if not images:
        return
        
    img_list = []
    for fp in images:
        try:
            img = Image.open(fp)
            img_rgb = img.convert('RGB')
            img_list.append(img_rgb)
        except Exception:
            pass
            
    if img_list:
        out_pdf = os.path.join(project_dir, 'visual_report.pdf')
        img_list[0].save(out_pdf, "PDF", resolution=150.0, save_all=True, append_images=img_list[1:])

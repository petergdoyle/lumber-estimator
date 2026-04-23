import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from PIL import Image
from markdown_pdf import MarkdownPdf, Section

# Modern, clean aesthetic for all document reports
USER_CSS = "html { font-family: Arial, Helvetica, sans-serif; }"

# Global Matplotlib Configuration for Arial-compatible charts
plt.rcParams['font.sans-serif'] = ['Arial', 'Liberation Sans', 'DejaVu Sans', 'sans-serif']
plt.rcParams['font.family'] = 'sans-serif'

def generate_buy_report_pdf(project_dir):
    md_path = os.path.join(project_dir, 'buy_report.md')
    pdf_path = os.path.join(project_dir, 'buy_report.pdf')
    if os.path.exists(md_path):
        try:
            pdf = MarkdownPdf(toc_level=2)
            with open(md_path, 'r') as f:
                content = f.read()
            pdf.add_section(Section(content), user_css=USER_CSS)
            pdf.save(pdf_path)
        except Exception as e:
            print(f"Warning: Failed to generate buy_report.pdf - {e}")

def generate_inventory_report_pdf(project_dir):
    md_path = os.path.join(project_dir, 'inventory_utilization.md')
    pdf_path = os.path.join(project_dir, 'inventory_utilization.pdf')
    if os.path.exists(md_path):
        try:
            pdf = MarkdownPdf(toc_level=2)
            with open(md_path, 'r') as f:
                content = f.read()
            pdf.add_section(Section(content), user_css=USER_CSS)
            pdf.save(pdf_path)
        except Exception as e:
            print(f"Warning: Failed to generate inventory_utilization.pdf - {e}")

def generate_verification_report_pdf(project_dir):
    md_path = os.path.join(project_dir, 'data_verification.md')
    pdf_path = os.path.join(project_dir, 'data_verification.pdf')
    if os.path.exists(md_path):
        try:
            pdf = MarkdownPdf(toc_level=2)
            with open(md_path, 'r') as f:
                content = f.read()
            pdf.add_section(Section(content), user_css=USER_CSS)
            pdf.save(pdf_path)
        except Exception as e:
            print(f"Warning: Failed to generate data_verification.pdf - {e}")

def generate_master_report_pdf(project_dir):
    md_path = os.path.join(project_dir, 'master_report.md')
    pdf_path = os.path.join(project_dir, 'master_report.pdf')
    if os.path.exists(md_path):
        try:
            pdf = MarkdownPdf(toc_level=2)
            with open(md_path, 'r') as f:
                content = f.read()
            pdf.add_section(Section(content), user_css=USER_CSS)
            pdf.save(pdf_path)
        except Exception as e:
            print(f"Warning: Failed to generate master_report.pdf - {e}")

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
    Also generates grayscale versions of all visualizations and a compiled grayscale PDF.
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
    gray_list = []
    
    gray_blueprints_dir = os.path.join(project_dir, 'blueprints_grayscale')
    os.makedirs(gray_blueprints_dir, exist_ok=True)
    
    for fp in images:
        try:
            img = Image.open(fp)
            img_rgb = img.convert('RGB')
            img_list.append(img_rgb)
            
            img_gray = img.convert('L')
            
            base_name = os.path.basename(fp)
            if base_name == 'capacity_chart.png':
                img_gray.save(os.path.join(project_dir, 'capacity_chart_grayscale.png'))
            else:
                img_gray.save(os.path.join(gray_blueprints_dir, base_name))
                
            gray_list.append(img_gray.convert('RGB'))
            
        except Exception:
            pass
            
    if img_list:
        out_pdf = os.path.join(project_dir, 'visual_report.pdf')
        img_list[0].save(out_pdf, "PDF", resolution=150.0, save_all=True, append_images=img_list[1:])
        
    if gray_list:
        out_pdf_gray = os.path.join(project_dir, 'visual_report_grayscale.pdf')
        gray_list[0].save(out_pdf_gray, "PDF", resolution=150.0, save_all=True, append_images=gray_list[1:])

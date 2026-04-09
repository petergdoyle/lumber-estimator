# Lumber Estimator

A powerful automated tool to help estimate material needs, generate 2D bin-packing layouts, and build itemized shopping lists for woodworking and building projects.

## Features

- **Automated Material Estimation**: Calculates Board Feet (BF) and Square Feet (SQFT), grouping by material.
- **Waste & Kerf Allowances**: Automatically pads requirements based on real-world cutting operations.
- **Inventory Subtraction**: Subtracts your current on-hand materials to build an exact, itemized shopping list.
- **2D Bin Packing & Blueprints**: Maps every single part onto available boards using intelligent bin-packing, generating visual cut-lists.
- **Reporting**: Generates summary CSVs, Markdown buy reports, and compiled visual PDFs (both color and print-friendly grayscale).

## Setup

Requires Python 3.

```bash
make setup
```

## Structure & Architecture

This tool uses a dynamic project-based data structure:
- `projects/`: Contains individual sub-folders for each of your distinct woodworking projects.
- `src/`: The core Python source code and estimation engine.

Inside a specific project folder (e.g., `projects/sample-dresser/`):
- **Inputs**: `project.yaml` (config rules), `parts.csv` (required cut list), and optionally `on-hand.csv` (current inventory).
- **Outputs**: All generated artifacts (`buy_report.pdf`, `visual_report_grayscale.pdf`, charts, and blueprints) are cleanly saved directly inside the project's folder.

## Usage

You execute the estimation engine by targeting a specific project directory using the Makefile:

```bash
# Run the bundled sample project to see it in action:
make project-sample-dresser
```

To see a list of all your available dynamically-detected projects, run:
```bash
make help
```

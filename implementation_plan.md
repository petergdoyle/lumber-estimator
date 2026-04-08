# Project-Based Lumber Estimator

This plan refines the estimator to support project-specific configurations via YAML and advanced lumber calculation logic.

## User Review Required

> [!IMPORTANT]
> **Project Organization:**
> We will move the project files into a dedicated directory: `data/kates-dresser/`.
> A `project.yaml` will control the inputs and waste allowances for each project.

> [!NOTE]
> **BF Calculation:**
> Board Feet (BF) will be calculated based on **Rough** dimensions:
> `(Rough Length * Rough Width * Nominal Thickness) / 144`.
> *Nominal Thickness* will be derived from the material moniker (e.g., "4/4" = 1", "8/4" = 2").

## Proposed Changes

### Data & Configuration

#### [NEW] [project.yaml](file:///Users/peterdoyle/Dev/lumber-estimator/data/kates-dresser/project.yaml)
Configuration for the "Kates Dresser" project:
- File mappings for parts and inventory.
- Waste allowances (configurable per project).

#### [MODIFY] Move CSV to `data/kates-dresser/`
Relocate `Kates Dresser - Overall.csv` to the project directory.

### Dependency Management

#### [MODIFY] [requirements.txt](file:///Users/peterdoyle/Dev/lumber-estimator/requirements.txt)
Add `PyYAML`.

### Core Logic

#### [NEW] [config.py](file:///Users/peterdoyle/Dev/lumber-estimator/src/config.py)
A module to load and validate the project YAML configuration.

#### [NEW] [dimensions.py](file:///Users/peterdoyle/Dev/lumber-estimator/src/dimensions.py)
Utility to handle fractions (e.g., "54 1/4") and unit conversions.

#### [MODIFY] [estimator.py](file:///Users/peterdoyle/Dev/lumber-estimator/src/estimator.py)
Revised to:
- Use project-specific waste settings.
- Group by thickness classes (4/4, 6/4, etc.).
- Calculate Board Feet and Square Feet totals.
- Handle "on-hand" inventory deductions (logic skeleton).

### Main Entry Point

#### [MODIFY] [main.py](file:///Users/peterdoyle/Dev/lumber-estimator/src/main.py)
Update to accept a project folder as an argument (e.g., `make run PROJECT=kates-dresser`).

## Open Questions

1. **Inventory Format:** For the "inventory-on-hand" file, should I assume the same columns as the parts list, or a simpler `Material, Thickness, BF_Available` format?
2. **Sheet Goods Yield:** For plywood, if we have on-hand inventory, should it be tracked by square footage or full/partial sheets (e.g., "half-sheet 48x48")?

## Verification Plan

### Automated Tests
- `tests/test_config.py`: Verify YAML loading.
- `tests/test_lumber_math.py`: Verify BF calculations with waste applied.

### Manual Verification
- `make run PROJECT=kates-dresser` should generate a detailed report in `output/kates-dresser/`.

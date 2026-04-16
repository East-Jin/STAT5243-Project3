# Architecture — Data Explorer

## Overview

Data Explorer is a Python Shiny (Core mode) web application with a four-stage reactive pipeline for data preprocessing and exploratory data analysis. A fifth tab provides an in-app User Guide.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        app.py                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │          ui.page_navbar (Flatly theme)                 │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────┐ │  │
│  │  │  User   │  Data    │  Data    │ Feature  │      │ │  │
│  │  │  Guide  │ Loading  │ Cleaning │   Eng    │ EDA  │ │  │
│  │  └─────────┴────┬─────┴────┬─────┴────┬─────┴──┬───┘ │  │
│  └─────────────────┼──────────┼──────────┼────────┼──────┘  │
│                    │          │          │        │          │
│  ┌─────────────────▼──────────▼──────────▼────────▼──────┐  │
│  │            SharedDataStore (reactive values)           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────┐       │  │
│  │  │ raw_data │  │ cleaned  │  │  engineered   │       │  │
│  │  │          │  │  _data   │  │    _data      │       │  │
│  │  └──────────┘  └──────────┘  └───────────────┘       │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Data Loading ──writes──► raw_data
                              │
                         reads│
                              ▼
Data Cleaning ──writes──► cleaned_data
                              │
                         reads│
                              ▼
Feature Eng ──writes──► engineered_data
                              │
                         reads│
                              ▼
EDA (reads raw, cleaned, or engineered — user selects)
```

Each downstream module has a **prerequisite guard** (marked `# === PREREQUISITE GUARD (DO NOT MODIFY) ===`). If the required upstream data is `None`, the module displays a warning instead of its controls.

## Shared Data Store Contract

The `SharedDataStore` class (in `shared/data_store.py`) holds reactive values for each pipeline stage:

| Reactive Value | Type | Set By | Read By |
|----------------|------|--------|---------|
| `raw_data` | `pd.DataFrame \| None` | Data Loading | Data Cleaning, EDA |
| `cleaned_data` | `pd.DataFrame \| None` | Data Cleaning | Feature Engineering, EDA |
| `engineered_data` | `pd.DataFrame \| None` | Feature Engineering | EDA |
| `data_info` | `dict` | Data Loading | All (for display) |

**Helper methods:**
- `get_latest_data()` — returns the most-processed DataFrame available (engineered > cleaned > raw)
- `get_latest_stage_name()` — returns `"engineered"`, `"cleaned"`, `"raw"`, or `"none"`
- `reset_downstream()` — clears cleaned_data and engineered_data when new raw data loads
- `has_downstream_data()` — checks if any downstream work exists (for confirmation dialogs)
- `dev_mode_init()` — pre-fills all stages with Titanic data for independent testing

## Module Details

### Data Loading (`modules/data_loading.py`)

**Reads:** nothing (entry point) | **Writes:** `raw_data`, `data_info`

- File upload supporting 5 formats: CSV, TSV, Excel (.xlsx/.xls), JSON, Parquet
- Auto-detection from file extension
- Two built-in datasets: Titanic (classification) and Ames Housing (regression)
- Dataset info bar with badges: filename, format, rows, columns, missing %, memory usage
- Two-tab main panel: Data Table (with interactive filter builder) and Column Summary
- Filter builder: categorical multi-select (with NA option) and numeric min/max range
- Active filters shown as removable chips with live row count
- Confirmation modal before replacing existing data (resets downstream)

### Data Cleaning (`modules/data_cleaning.py`)

**Reads:** `raw_data` | **Writes:** `cleaned_data`

Ten-step interactive pipeline:

1. **Standardize Missing Values** — convert tokens ("", NA, null, ?, etc.) to NaN
2. **Format Standardization** — snake_case columns, trim whitespace, lowercase, strip characters, auto-convert to numeric
3. **Drop Columns** — multi-select column removal
4. **Handle Missing Values** — per-column imputation (mean, median, mode, zero, constant, ffill, bfill) and bulk strategies (drop rows, drop columns above threshold, auto-impute)
5. **Handle Duplicates** — detect and remove exact duplicate rows
6. **Remap Categorical Values** — fix typos and merge labels
7. **Change Column Types** — convert to numeric, boolean, categorical, or text
8. **Handle Outliers** — IQR (remove/cap), Z-score (remove/cap), Percentile (cap)
9. **Scale Numeric Features** — StandardScaler or MinMaxScaler with column exclusion
10. **Encode Categorical Features** — One-Hot (with drop_first option) or Label encoding

Visual feedback via 5 tabs: Preview, Missing Values chart, Distributions histogram, Outliers boxplot, Info table. Multi-step undo (up to 20 snapshots). Explicit Apply & Save workflow.

### Feature Engineering (`modules/feature_engineering.py`)

**Reads:** `cleaned_data` | **Writes:** `engineered_data`

Three operation categories:

- **Single-Column Transforms:** Log, Log1p, Square Root, Square, Z-Score, Min-Max, Binning (2–10 bins)
- **Two-Column Combinations:** Add, Multiply, Ratio
- **Date/Time Extraction:** Year, Month, Day, Day of Week, Hour, Minute, Quarter, Is Weekend, Day of Year

Features: before/after distribution plots, custom feature naming, feature history sidebar, multi-step undo, reset to cleaned data, and Save to Pipeline workflow.

### Exploratory Data Analysis (`modules/eda.py`)

**Reads:** `raw_data`, `cleaned_data`, `engineered_data` (user selects) | **Writes:** nothing

- Data stage selector to compare any pipeline stage
- Dynamic numeric range and categorical value filters
- Six interactive Plotly chart types: Scatter (with optional OLS trendline), Bar (average), Box, Histogram (adjustable bins), Violin, Pie
- Pair plot (scatter matrix) with selectable columns
- Correlation heatmap with adjustable column limit and RdBu_r color scale
- Summary statistics table (describe with all dtypes)

### User Guide (`modules/user_guide.py`)

**UI only — no server component**

In-app documentation with a step-by-step walkthrough of all four pipeline stages, supported file formats table, and usage tips (resizable sidebars, tooltips, undo support, prerequisite guards, etc.).

## File Structure

```
app.py                          # Entry point — navbar, store init, module wiring
modules/
    __init__.py                 # Re-exports all module UIs and servers
    user_guide.py               # In-app documentation (UI only)
    data_loading.py             # Upload, format detection, filters, column summary
    data_cleaning.py            # 10-step cleaning pipeline
    feature_engineering.py      # Transforms, combinations, date extraction
    eda.py                      # Interactive plots, pair plot, heatmap, statistics
shared/
    __init__.py                 # Re-exports SharedDataStore and sample dataset helpers
    data_store.py               # SharedDataStore class with reactive values
    sample_datasets.py          # Titanic & Ames Housing loaders from bundled CSVs
data/
    titanic.csv                 # Built-in sample dataset (classification)
    ames_housing.csv            # Built-in sample dataset (regression)
docs/
    ARCHITECTURE.md             # This file
report/
    Report.md                   # Project report (Markdown)
    Report.pdf                  # Project report (PDF)
requirements.txt                # Python dependencies
README.md                       # Quick-start setup guide
```

## Module Convention

Every module exports `*_ui()` and `*_server(input, output, session, shared_store, app_session)` using `@module.ui` / `@module.server` decorators:

```python
@module.ui
def my_module_ui():
    return ui.layout_sidebar(
        ui.sidebar(...),     # Controls
        # Main panel outputs
    )

@module.server
def my_module_server(input, output, session, shared_store, app_session=None):
    # === PREREQUISITE GUARD (DO NOT MODIFY) ===
    @render.ui
    def guard_message():
        if shared_store.some_data() is None:
            return ui.div(...)    # Warning message
        return ui.TagList()
    # === END GUARD ===

    # ... implementation ...
```

## Tech Stack

- **Framework:** Python Shiny (Core mode) with `@module` decorators
- **UI Theme:** shinyswatch (Bootstrap Flatly)
- **Data:** pandas, NumPy
- **Visualization:** Plotly (interactive), Matplotlib + Seaborn (static in cleaning tabs)
- **ML/Preprocessing:** scikit-learn (scaling, encoding), statsmodels (OLS trendlines)
- **File I/O:** openpyxl (Excel), PyArrow (Parquet)
- **Deployment:** shinyapps.io via rsconnect-python
- **Python:** 3.11 (managed via [uv](https://docs.astral.sh/uv/))

## Dev Mode

Pre-fill all pipeline stages with Titanic sample data for independent module testing:

```bash
DEV_MODE=true shiny run app_B.py
```

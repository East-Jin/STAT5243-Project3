---
geometry: margin=0.6in
fontsize: 10pt
linestretch: 1.0
header-includes:
  - \setlength{\parskip}{2pt}
  - \setlength{\parindent}{0pt}
  - \pagestyle{empty}
  - \usepackage{fancyvrb}
  - \let\olditemize\itemize
  - \renewcommand{\itemize}{\olditemize\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}\setlength{\topsep}{0pt}}
  - \let\oldenumerate\enumerate
  - \renewcommand{\enumerate}{\oldenumerate\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}\setlength{\topsep}{0pt}}
---

# Project 2: Web Application Development and Deployment

**Team 20 — STAT 5243, Spring 2026**

**Deployed App:** https://zd2372.shinyapps.io/data_explorer/

**GitHub Repository:** https://github.com/East-Jin/STAT5243-Project2

## 1. Application Overview

Data Explorer is a full-featured, production-grade web application built with Python Shiny (Core mode) that guides users through the complete data science preprocessing workflow — from raw file ingestion to publication-ready exploratory analysis — entirely in the browser with zero coding required. The application implements a four-stage reactive pipeline — **Data Loading**, **Data Cleaning**, **Feature Engineering**, and **EDA** — where each stage reads from and writes to a centralized `SharedDataStore` of reactive values, ensuring that changes propagate downstream automatically while prerequisite guards prevent users from accessing stages with missing upstream data. A polished UI powered by the Flatly Bootstrap theme (shinyswatch), interactive Plotly visualizations, real-time toast notifications, contextual info-icon popovers, and a built-in User Guide tab collectively deliver a smooth, intuitive experience suitable for both beginners learning data wrangling and analysts prototyping preprocessing pipelines.

\begin{center}
\small
\begin{BVerbatim}
+-------------------------------------------------------------+
|                           app.py                            |
|  +-------------------------------------------------------+  |
|  |                     ui.page_navbar                    |  |
|  |  +---------+-----------+----------+---------+------+  |  |
|  |  |  User   |   Data    |   Data   | Feature |      |  |  |
|  |  |  Guide  |  Loading  | Cleaning |   Eng   | EDA  |  |  |
|  |  +---------+-----+-----+----+-----+---+-----+--+---+  |  |
|  +-------------------+----------+----------+-------+-----+  |
|                      |          |          |       |        |
|  +-------------------v----------v----------v-------v-----+  |
|  |                    SharedDataStore                    |  |
|  |     +----------+  +----------+  +---------------+     |  |
|  |     | raw_data |  | cleaned_ |  | engineered_   |     |  |
|  |     |          |  |   data   |  |     data      |     |  |
|  |     +----------+  +----------+  +---------------+     |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
\end{BVerbatim}
\normalsize
\end{center}

## 2. Key Features

### 2.1 Loading Datasets
- Supports five file formats: CSV, TSV, Excel (.xlsx/.xls), JSON, and Parquet with automatic format detection.
- Two built-in sample datasets (Titanic for classification, Ames Housing for regression) for immediate exploration.
- Info bar displays filename, format, row/column counts, missing-value percentage, and memory usage.
- Interactive filter builder with categorical multi-select and numeric min/max range filters, shown as removable chips.
- Column Summary tab with per-column statistics (dtype, missing %, quartiles, mean, std, mode).

### 2.2 Data Cleaning and Preprocessing
- Ten-step interactive pipeline: standardize missing tokens, format standardization (snake_case, trim, lowercase), drop columns, per-column and bulk imputation, duplicate removal, categorical remapping, type conversion, outlier handling (IQR/Z-score/Percentile), scaling (Standard/MinMax), and encoding (One-Hot/Label).
- Real-time visual feedback via five tabs: Preview, Missing Values bar chart, Distributions histogram, Outliers boxplot, and column Info table.
- Multi-step undo (up to 20 snapshots) and an explicit Apply & Save button to commit changes to the pipeline.

### 2.3 Feature Engineering
- Single-column transforms: Log, Log1p, Square Root, Square, Z-Score, Min-Max Scaling, and Binning (adjustable bin count).
- Two-column combinations: Add, Multiply, and Ratio operations for creating interaction features.
- Date/time extraction: Year, Month, Day, Day of Week, Hour, Minute, Quarter, Is Weekend, and Day of Year.
- Before/after distribution comparison plots, custom feature naming, feature history tracking, undo, and reset to cleaned data.

### 2.4 Exploratory Data Analysis (EDA)
- Data stage selector lets users compare raw, cleaned, or engineered data side by side.
- Six interactive Plotly chart types: Scatter (with optional OLS trendline), Bar (average), Box, Histogram (adjustable bins), Violin, and Pie.
- Dynamic numeric range and categorical value filters that update in real time.
- Pair plot (scatter matrix) for multi-variable relationships and correlation heatmap with adjustable column limit.
- Summary statistics table with count, mean, std, min, quartiles, max, unique, top, and frequency.

### 2.5 User Interface (UI) and User Experience (UX)
- Navbar layout with resizable sidebars, info-icon popovers providing contextual help, and toast notifications for all operations.
- User Guide tab with a complete walkthrough of all four pipeline stages, supported formats table, and usage tips.
- Prerequisite guards on each tab prevent users from skipping pipeline stages, displaying clear warning messages.
- Well-structured layout with consistent styling across all modules using the Flatly Bootstrap theme (shinyswatch).

### 2.6 Web Application Functionality (Interactivity, Usability, and Responsiveness)
- Highly interactive: users dynamically manipulate data and visualizations across all four pipeline stages with immediate feedback.
- Fast response times: reactive computations update outputs with minimal lag, even on large datasets.
- Dynamic UI rendering: controls, filters, and chart options adjust automatically based on the current data and user selections.
- Smooth end-to-end workflow: changes in upstream stages propagate downstream through the SharedDataStore, and confirmation dialogs protect against accidental data loss.

## 3. How to Use

1. **Load Data** — Upload a file (CSV, TSV, Excel, JSON, or Parquet) or select a built-in dataset. Review the data table, apply filters to narrow rows, and inspect the Column Summary for per-column statistics.
2. **Clean Data** — Walk through the ten-step pipeline (missing tokens, formatting, drop columns, imputation, duplicates, remapping, type conversion, outliers, scaling, encoding). Use the five feedback tabs to verify, then click *Apply & Save*.
3. **Engineer Features** — Create new columns via transforms, two-column combinations, or date extraction. Compare before/after distributions and save to the pipeline.
4. **Explore (EDA)** — Select a pipeline stage, apply filters, and choose from six chart types, pair plots, heatmaps, or statistics.

## 4. Team Member Contributions

\noindent
\begin{tabular}{p{0.15\textwidth} p{0.07\textwidth} p{0.18\textwidth} p{0.48\textwidth}}
\hline
\textbf{Team Member} & \textbf{UNI} & \textbf{Module} & \textbf{Responsibilities} \\
\hline
Zhewei Deng & zd2372 & Data Loading & File upload, format detection, built-in datasets, filters, column summary; project scaffolding, shared data store, UI enhancements, User Guide, integration \& deployment \\
Guichen Zheng & gz2400 & Data Cleaning & 10-step cleaning pipeline, imputation, scaling, encoding, outlier handling \\
Qingyue Wang & qw2465 & Feature Engineering & Transforms, column combinations, date extraction, before/after plots \\
Xiang Li & xl3548 & EDA & Interactive plots, pair plots, correlation heatmap, summary statistics \\
\hline
\end{tabular}

All members contributed equally, collaborating on shared architecture, User Guide, UI styling, testing, and deployment.

## 5. Technology Stack

Python Shiny (Core mode), shinyswatch (Flatly theme), pandas, NumPy, Plotly, Matplotlib, Seaborn, scikit-learn, statsmodels, openpyxl, PyArrow. Deployed on shinyapps.io via rsconnect-python.

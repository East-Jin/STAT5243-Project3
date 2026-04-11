"""
User Guide Module

Provides clear instructions and tooltips to guide users through the
application. Displayed as the first tab per the project requirements.
"""

from __future__ import annotations

from shiny import module, ui


def _icon_badge(icon: str, text: str) -> ui.Tag:
    return ui.div(
        ui.tags.span(icon, style="font-size:1.6rem;"),
        ui.tags.span(text, style="font-weight:600; font-size:0.95rem;"),
        style="display:flex; align-items:center; gap:0.5rem;",
    )


def _step_card(number: str, title: str, icon: str, body: ui.TagChild) -> ui.Tag:
    return ui.div(
        ui.div(
            ui.div(
                ui.tags.span(
                    number,
                    style=(
                        "background:#2c3e50; color:#fff; border-radius:50%;"
                        "width:2rem; height:2rem; display:inline-flex;"
                        "align-items:center; justify-content:center; font-weight:700;"
                        "font-size:0.95rem; flex-shrink:0;"
                    ),
                ),
                ui.tags.span(
                    f"{icon}  {title}",
                    style="font-weight:700; font-size:1.1rem;",
                ),
                style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.6rem;",
            ),
            body,
            style="padding:1.2rem;",
        ),
        class_="card h-100 shadow-sm",
    )


def _format_table() -> ui.Tag:
    rows = [
        ("CSV / TSV", ".csv .tsv", "Comma or tab-separated text files"),
        ("Excel", ".xlsx .xls", "Microsoft Excel workbooks"),
        ("JSON", ".json", "JavaScript Object Notation"),
        ("Parquet", ".parquet", "Columnar storage (Apache Arrow)"),
    ]
    return ui.tags.table(
        ui.tags.thead(
            ui.tags.tr(
                ui.tags.th("Format", style="padding:0.4rem 0.8rem;"),
                ui.tags.th("Extensions", style="padding:0.4rem 0.8rem;"),
                ui.tags.th("Notes", style="padding:0.4rem 0.8rem;"),
            ),
            style="background:#f8f9fa;",
        ),
        ui.tags.tbody(
            *[
                ui.tags.tr(
                    ui.tags.td(fmt, style="padding:0.4rem 0.8rem; font-weight:600;"),
                    ui.tags.td(
                        ui.tags.code(ext),
                        style="padding:0.4rem 0.8rem;",
                    ),
                    ui.tags.td(note, style="padding:0.4rem 0.8rem;"),
                )
                for fmt, ext, note in rows
            ]
        ),
        class_="table table-bordered table-sm mb-0",
        style="font-size:0.9rem;",
    )


@module.ui
def user_guide_ui():
    return ui.div(
        ui.div(
            # ── Hero section ──
            ui.div(
                ui.div(
                    ui.h2(
                        "Welcome to Data Explorer",
                        style="margin-bottom:0.3rem; font-weight:700;",
                    ),
                    ui.p(
                        "An interactive toolkit for loading, cleaning, engineering, "
                        "and exploring datasets — all from your browser.",
                        style="font-size:1.05rem; opacity:0.92; margin-bottom:0;",
                    ),
                    style=(
                        "background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);"
                        "color: #fff; border-radius: 0.75rem; padding: 2rem 2.5rem;"
                        "margin-bottom: 1.5rem;"
                    ),
                ),
            ),

            # ── Workflow overview ──
            ui.h4("How It Works", style="font-weight:700; margin-bottom:0.8rem;"),
            ui.p(
                "The app follows a sequential pipeline. Complete each step before "
                "moving to the next — the data flows forward automatically. "
                "Each tab has a prerequisite guard that prevents access until the "
                "required data is ready.",
                style="margin-bottom:1rem; color:#555;",
            ),

            ui.div(
                # ── Step 1: Data Loading ──
                ui.div(
                    _step_card(
                        "1", "Load Dataset", "\U0001F4C2",
                        ui.TagList(
                            ui.tags.ul(
                                ui.tags.li(
                                    "Choose a data source via the radio toggle: ",
                                    ui.tags.b("Upload a File"),
                                    " (drag-and-drop or browse) or ",
                                    ui.tags.b("Built-in Dataset"),
                                    " (Titanic for classification, Ames Housing for regression).",
                                ),
                                ui.tags.li(
                                    "Five file formats are supported: CSV, TSV, Excel, JSON, and Parquet.",
                                ),
                                ui.tags.li(
                                    "Click ", ui.tags.b("Load Dataset"),
                                    " to confirm. If a previous dataset exists, a confirmation dialog appears before overwriting.",
                                ),
                                ui.tags.li(
                                    "After loading, an info bar shows the dataset name, format, row/column counts, "
                                    "overall missing percentage, and memory usage.",
                                ),
                                ui.tags.li(
                                    "Two main tabs: ",
                                    ui.tags.b("Data Table"),
                                    " (full paginated view with horizontal scrolling) and ",
                                    ui.tags.b("Column Summary"),
                                    " (per-column statistics: dtype, missing count/%, unique values, "
                                    "min, Q1, median, Q3, max, mean, std, and top value for categorical columns).",
                                ),
                                ui.tags.li(
                                    "Use the ", ui.tags.b("custom filter builder"),
                                    " on the Data Table tab: click ",
                                    ui.tags.em("+ Add Filter"),
                                    ", select a column, then set multi-select values for categorical columns "
                                    "(including NA) or min/max range for numeric columns. Active filters appear "
                                    "as removable chips with a live row count.",
                                ),
                                ui.tags.li(
                                    "Click ", ui.tags.b("Proceed to Data Cleaning"),
                                    " (appears after data loads) to move to the next tab.",
                                ),
                                style="margin-bottom:0; padding-left:1.2rem; font-size:0.9rem;",
                            ),
                        ),
                    ),
                    class_="col-md-6 mb-3",
                ),

                # ── Step 2: Data Cleaning ──
                ui.div(
                    _step_card(
                        "2", "Clean & Pre-process", "\U0001F9F9",
                        ui.TagList(
                            ui.p(
                                "A 10-step interactive cleaning pipeline. Each step has its own "
                                "Apply button — apply them in any order via the sidebar.",
                                class_="text-muted small mb-1",
                            ),
                            ui.tags.ol(
                                ui.tags.li(
                                    ui.tags.b("Standardize Missing Values"),
                                    " — convert tokens (NA, null, None, ?, -, empty strings, etc.) "
                                    "to true missing values. Optionally trim whitespace first.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Format Standardization"),
                                    " — normalize column names (snake_case), trim/lowercase text, "
                                    "strip unwanted characters, and auto-convert text columns to numeric.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Drop Columns"),
                                    " — remove unnecessary columns (e.g. IDs, constants) via multi-select.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Handle Missing Values"),
                                    " — per-column impute (mean, median, mode, zero, constant, forward/backward fill) "
                                    "or bulk strategies (drop rows, drop columns above threshold, impute all).",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Handle Duplicates"),
                                    " — remove exact duplicate rows.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Remap Categorical Values"),
                                    " — fix typos or merge similar labels by selecting a value and its replacement.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Change Column Types"),
                                    " — convert columns to numeric, boolean, categorical, or text.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Handle Outliers"),
                                    " — IQR (remove/cap), Z-score (remove/cap), or percentile capping.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Scale Numeric Features"),
                                    " — StandardScaler or MinMaxScaler, with the option to exclude specific columns.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Encode Categorical Features"),
                                    " — one-hot encoding (with optional drop-first) or label encoding.",
                                ),
                                style="margin-bottom:0.3rem; padding-left:1.2rem; font-size:0.88rem;",
                            ),
                            ui.p(
                                "Visualization tabs: Preview, Missing Values (bar chart + table), "
                                "Distributions (histogram per column), Outliers (boxplot per column), "
                                "and Column Info. An ", ui.tags.b("Undo"),
                                " button reverts the last step. Click ",
                                ui.tags.b("Apply & Save"), " to push cleaned data to the pipeline.",
                                class_="small mb-0",
                            ),
                        ),
                    ),
                    class_="col-md-6 mb-3",
                ),

                # ── Step 3: Feature Engineering ──
                ui.div(
                    _step_card(
                        "3", "Feature Engineering", "\u2699\uFE0F",
                        ui.TagList(
                            ui.p(
                                "Three operation categories, each with real-time before/after distribution plots.",
                                class_="text-muted small mb-1",
                            ),
                            ui.tags.ul(
                                ui.tags.li(
                                    ui.tags.b("Single-Column Transforms"),
                                    " — log (ln), log1p (ln(1+x)), square root, square, "
                                    "Z-score standardization, min-max scaling, or binning (adjustable bin count).",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Combine Two Columns"),
                                    " — add (x\u2081 + x\u2082), multiply (x\u2081 \u00d7 x\u2082), "
                                    "or ratio (x\u2081 / x\u2082). Zeros in denominator become NaN.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Date / Time Extraction"),
                                    " — extract year, month, day, day-of-week, hour, minute, "
                                    "quarter, is-weekend, or day-of-year from datetime columns.",
                                ),
                                style="margin-bottom:0.3rem; padding-left:1.2rem; font-size:0.9rem;",
                            ),
                            ui.p(
                                "Each operation shows a contextual explanation in the sidebar. "
                                "Optionally set a ", ui.tags.b("custom feature name"),
                                " or let one auto-generate. ",
                                "Click ", ui.tags.b("Apply"),
                                " to add the feature to the working table, then ",
                                ui.tags.b("Save to Pipeline"),
                                " to push it to EDA. Use ",
                                ui.tags.b("Undo Last Apply"),
                                " to revert, or ",
                                ui.tags.b("Reset to Cleaned Data"),
                                " to start over. A ", ui.tags.b("Feature History"),
                                " panel tracks all applied features.",
                                class_="small mb-0",
                            ),
                        ),
                    ),
                    class_="col-md-6 mb-3",
                ),

                # ── Step 4: EDA ──
                ui.div(
                    _step_card(
                        "4", "Exploratory Data Analysis", "\U0001F4CA",
                        ui.TagList(
                            ui.tags.ul(
                                ui.tags.li(
                                    "Choose which pipeline stage to analyse: ",
                                    ui.tags.b("Raw"), ", ",
                                    ui.tags.b("Cleaned"), ", or ",
                                    ui.tags.b("Engineered"), " data.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Filter data"),
                                    " dynamically by numeric range (slider) or categorical values (multi-select).",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Interactive Plot"),
                                    " — choose from scatter plot (with optional OLS trendline), "
                                    "bar chart (average), box plot, histogram (adjustable bins), "
                                    "violin plot, or pie chart. Assign X/Y variables and an optional "
                                    "color/group-by column.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Pair Plot"),
                                    " — scatter matrix of selected numeric columns to visualise "
                                    "pairwise relationships at a glance.",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Correlation Heatmap"),
                                    " — colour-coded matrix of numeric column correlations "
                                    "(adjustable max column count).",
                                ),
                                ui.tags.li(
                                    ui.tags.b("Summary Statistics"),
                                    " — descriptive statistics table (count, mean, std, min, "
                                    "25%, 50%, 75%, max, unique, top, freq) for all columns.",
                                ),
                                ui.tags.li(
                                    "Download any Plotly chart as an image using the camera icon "
                                    "in the plot toolbar.",
                                ),
                                style="margin-bottom:0; padding-left:1.2rem; font-size:0.9rem;",
                            ),
                        ),
                    ),
                    class_="col-md-6 mb-3",
                ),
                class_="row",
            ),

            # ── Supported formats ──
            ui.h4("Supported File Formats", style="font-weight:700; margin-top:0.5rem; margin-bottom:0.8rem;"),
            _format_table(),

            # ── Tips ──
            ui.div(
                ui.h4("\U0001F4A1  Tips", style="font-weight:700; margin-bottom:0.6rem;"),
                ui.tags.ul(
                    ui.tags.li(
                        ui.tags.b("Resize sidebars"),
                        " — drag the right edge of any sidebar to adjust its width.",
                    ),
                    ui.tags.li(
                        ui.tags.b("Tooltips & \u2139\uFE0F icons"),
                        " — look for the info icon at the top-right of each panel for tab-specific guidance.",
                    ),
                    ui.tags.li(
                        ui.tags.b("Notifications"),
                        " — success and error messages appear at the top of the screen "
                        "after every operation.",
                    ),
                    ui.tags.li(
                        ui.tags.b("Undo"),
                        " — both Data Cleaning and Feature Engineering tabs support "
                        "multi-step undo (up to 20 steps).",
                    ),
                    ui.tags.li(
                        ui.tags.b("Sequential flow"),
                        " — each tab unlocks once its prerequisite data is ready. "
                        "A ", ui.tags.em("Proceed"), " button appears when you can advance.",
                    ),
                    ui.tags.li(
                        ui.tags.b("Pipeline stages"),
                        " — the EDA tab can read from any stage (raw, cleaned, engineered) "
                        "so you can compare data at different points in the pipeline.",
                    ),
                    style="padding-left:1.2rem; font-size:0.93rem; margin-bottom:0;",
                ),
                style=(
                    "background:#f0f7ff; border-left:4px solid #3498db;"
                    "border-radius:0.5rem; padding:1rem 1.2rem; margin-top:1.2rem;"
                ),
            ),

            style="max-width:960px; margin:0 auto; padding:1.5rem 1rem;",
        ),
        style="overflow-y:auto; height:100%;",
    )

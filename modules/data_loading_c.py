"""
Data Loading Module — Member 1

Reads: nothing (entry point)
Writes: shared_store.raw_data, shared_store.data_info
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from shiny import Inputs, Outputs, Session, module, reactive, render, ui

from shared.sample_datasets import BUILTIN_DATASETS, BUILTIN_LABELS

ACCEPTED_EXTENSIONS = [".csv", ".tsv", ".xlsx", ".xls", ".json", ".parquet"]

_CATEGORICAL_THRESHOLD = 30


def _read_file(filepath: str, filename: str) -> pd.DataFrame:
    """Auto-detect format from extension and read into a DataFrame."""
    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        return pd.read_csv(filepath)
    elif ext == ".tsv":
        return pd.read_csv(filepath, sep="\t")
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(filepath)
    elif ext == ".json":
        return pd.read_json(filepath)
    elif ext == ".parquet":
        return pd.read_parquet(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _format_from_filename(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    fmt_map = {
        ".csv": "CSV", ".tsv": "TSV", ".xlsx": "Excel",
        ".xls": "Excel", ".json": "JSON", ".parquet": "Parquet",
    }
    return fmt_map.get(ext, ext.upper())


def _build_column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build a per-column summary table with stats appropriate to each dtype."""
    rows = []
    for col in df.columns:
        series = df[col]
        missing_count = int(series.isnull().sum())
        total = len(series)
        row = {
            "Column": col,
            "Dtype": str(series.dtype),
            "Non-Null": total - missing_count,
            "Missing": missing_count,
            "Missing %": round(missing_count / total * 100, 1) if total > 0 else 0,
            "Unique": int(series.nunique()),
        }
        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            row.update({
                "Min": round(desc.get("min", np.nan), 4),
                "Q1": round(desc.get("25%", np.nan), 4),
                "Median": round(desc.get("50%", np.nan), 4),
                "Q3": round(desc.get("75%", np.nan), 4),
                "Max": round(desc.get("max", np.nan), 4),
                "Mean": round(desc.get("mean", np.nan), 4),
                "Std": round(desc.get("std", np.nan), 4),
                "Top Value": "",
            })
        else:
            mode_val = series.mode()
            top = str(mode_val.iloc[0]) if len(mode_val) > 0 else ""
            row.update({
                "Min": "", "Q1": "", "Median": "", "Q3": "",
                "Max": "", "Mean": "", "Std": "",
                "Top Value": top,
            })
        rows.append(row)
    return pd.DataFrame(rows)


def _is_categorical(series: pd.Series) -> bool:
    """Return True if the column should use a categorical (dropdown) filter."""
    if pd.api.types.is_bool_dtype(series):
        return True
    if not pd.api.types.is_numeric_dtype(series):
        return True
    return int(series.nunique()) <= _CATEGORICAL_THRESHOLD


# =============================================================================
# UI
# =============================================================================

_FILE_INPUT_CSS = ui.tags.style(
    ".progress { height: 1.5rem; }"
    ".progress-bar { line-height: 1.5rem; font-size: 0.85rem; }"
)


@module.ui
def data_loading_ui():
    return ui.layout_sidebar(
        ui.sidebar(
            _FILE_INPUT_CSS,
            ui.h4("Load a Dataset"),
            ui.hr(),
            ui.input_radio_buttons(
                "source_mode",
                "Data Source",
                choices={"upload": "Upload a File"},
                selected="upload",
            ),
            ui.output_ui("source_controls"),
            ui.hr(),
            ui.input_action_button("confirm_load", "Load Dataset", class_="btn-primary w-100"),
            width=320,
        ),
        # Main panel
        ui.output_ui("dataset_info"),
        ui.output_ui("main_content"),
        ui.output_ui("next_step_btn"),
        fillable=True,
    )


# =============================================================================
# Server
# =============================================================================

@module.server
def data_loading_server(
    input: Inputs, output: Outputs, session: Session,
    shared_store, app_session=None,
):
    pending_load: reactive.value[dict | None] = reactive.value(None)
    active_filters: reactive.value[list[dict]] = reactive.value([])
    show_filter_form: reactive.value[bool] = reactive.value(False)

    # -- Sidebar: conditional controls based on source mode --

    @render.ui
    def source_controls():
        if input.source_mode() == "upload":
            return ui.div(
                ui.input_file(
                    "file_upload",
                    "Choose a file",
                    accept=ACCEPTED_EXTENSIONS,
                ),
                ui.p(
                    "Supported: CSV, TSV, Excel, JSON, Parquet",
                    class_="text-muted small",
                ),
            )
        else:
            return ui.input_select(
                "builtin_dataset",
                "Select Dataset",
                choices={"": "— select —", **BUILTIN_LABELS},
            )

    # -- Confirm Load button handler --

    @reactive.effect
    @reactive.event(input.confirm_load)
    def _on_confirm_load():
        mode = input.source_mode()

        if mode == "upload":
            file_infos = input.file_upload()
            if not file_infos:
                ui.notification_show(
                    "Please select a file first.",
                    type="warning",
                )
                return
            file_info = file_infos[0]
            pending_load.set({
                "type": "upload",
                "filepath": file_info["datapath"],
                "filename": file_info["name"],
            })
        else:
            name = input.builtin_dataset()
            if not name or name not in BUILTIN_DATASETS:
                ui.notification_show(
                    "Please select a dataset from the dropdown.",
                    type="warning",
                )
                return
            pending_load.set({
                "type": "builtin",
                "name": name,
            })

        if shared_store.has_downstream_data():
            ui.modal_show(
                ui.modal(
                    ui.p(
                        "Loading a new dataset will erase all downstream work "
                        "(cleaning, feature engineering). Are you sure?"
                    ),
                    ui.div(
                        ui.input_action_button(
                            "modal_confirm", "Confirm",
                            class_="btn-danger me-2",
                        ),
                        ui.input_action_button(
                            "modal_cancel", "Cancel",
                            class_="btn-secondary",
                        ),
                        class_="d-flex",
                    ),
                    title="Replace current dataset?",
                    easy_close=False,
                    footer=None,
                ),
            )
        else:
            _execute_load()

    @reactive.effect
    @reactive.event(input.modal_confirm)
    def _on_modal_confirm():
        ui.modal_remove()
        shared_store.reset_downstream()
        _execute_load()

    @reactive.effect
    @reactive.event(input.modal_cancel)
    def _on_modal_cancel():
        ui.modal_remove()
        pending_load.set(None)

    def _execute_load():
        load_info = pending_load()
        if load_info is None:
            return

        try:
            if load_info["type"] == "upload":
                df = _read_file(load_info["filepath"], load_info["filename"])
                fname = load_info["filename"]
                fmt = _format_from_filename(fname)
            else:
                name = load_info["name"]
                df = BUILTIN_DATASETS[name]()
                fname = BUILTIN_LABELS.get(name, name)
                fmt = "Built-in"

            if df.empty:
                ui.notification_show("The file is empty — no rows found.", type="error")
                return

            shared_store.raw_data.set(df)
            shared_store.data_info.set({
                "filename": fname,
                "format": fmt,
                "rows": df.shape[0],
                "columns": df.shape[1],
            })
            active_filters.set([])
            show_filter_form.set(False)
            ui.notification_show(
                f"Loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns",
                type="message",
            )
        except Exception as e:
            ui.notification_show(f"Error loading file: {e}", type="error")
        finally:
            pending_load.set(None)

    # -- Filtered DataFrame --

    @reactive.calc
    def filtered_df():
        df = shared_store.raw_data()
        if df is None:
            return None
        filters = active_filters()
        for f in filters:
            col = f["column"]
            if col not in df.columns:
                continue
            if f["type"] == "categorical":
                values = f["values"]
                include_na = "(NA)" in values
                non_na_values = [v for v in values if v != "(NA)"]
                mask = df[col].astype(str).isin(non_na_values)
                if include_na:
                    mask = mask | df[col].isnull()
                df = df[mask]
            elif f["type"] == "numeric":
                if f.get("min") is not None:
                    df = df[df[col] >= f["min"]]
                if f.get("max") is not None:
                    df = df[df[col] <= f["max"]]
        return df

    # -- Filter builder events --

    @reactive.effect
    @reactive.event(input.add_filter_btn)
    def _show_filter_form():
        show_filter_form.set(True)

    @reactive.effect
    @reactive.event(input.cancel_filter_btn)
    def _hide_filter_form():
        show_filter_form.set(False)

    @reactive.effect
    @reactive.event(input.apply_filter_btn)
    def _apply_filter():
        df = shared_store.raw_data()
        if df is None:
            return
        try:
            col = input.filter_col_select()
        except Exception:
            ui.notification_show("Please select a column.", type="warning")
            return
        if not col or col not in df.columns:
            ui.notification_show("Please select a column.", type="warning")
            return

        series = df[col]
        if _is_categorical(series):
            try:
                values = list(input.filter_cat_values())
            except Exception:
                values = []
            if not values:
                ui.notification_show("Please select at least one value.", type="warning")
                return
            new_filter = {"column": col, "type": "categorical", "values": values}
        else:
            try:
                min_val = input.filter_num_min()
            except Exception:
                min_val = None
            try:
                max_val = input.filter_num_max()
            except Exception:
                max_val = None
            if min_val is None and max_val is None:
                ui.notification_show("Please set a min or max value.", type="warning")
                return
            new_filter = {"column": col, "type": "numeric", "min": min_val, "max": max_val}

        current = active_filters()
        updated = [f for f in current if f["column"] != col]
        updated.append(new_filter)
        active_filters.set(updated)
        show_filter_form.set(False)

    @reactive.effect
    @reactive.event(input.remove_filter)
    def _remove_filter():
        idx = input.remove_filter()
        try:
            idx = int(idx)
        except (TypeError, ValueError):
            return
        current = active_filters()
        if 0 <= idx < len(current):
            updated = current[:idx] + current[idx + 1:]
            active_filters.set(updated)

    # -- Info bar --

    @render.ui
    def dataset_info():
        info = shared_store.data_info()
        if not info:
            return ui.p(
                "No dataset loaded yet. Select a source and click Load Dataset.",
                class_="text-muted",
            )
        df = shared_store.raw_data()
        missing_pct = 0.0
        mem_usage = "—"
        if df is not None:
            total_cells = df.shape[0] * df.shape[1]
            if total_cells > 0:
                missing_pct = round(df.isnull().sum().sum() / total_cells * 100, 1)
            mem_bytes = df.memory_usage(deep=True).sum()
            if mem_bytes < 1024 * 1024:
                mem_usage = f"{mem_bytes / 1024:.0f} KB"
            else:
                mem_usage = f"{mem_bytes / (1024 * 1024):.1f} MB"

        return ui.div(
            ui.tags.span(f"Dataset: {info['filename']}", class_="badge bg-success me-2"),
            ui.tags.span(f"Format: {info.get('format', '—')}", class_="badge bg-secondary me-2"),
            ui.tags.span(f"Rows: {info['rows']}", class_="badge bg-info me-2"),
            ui.tags.span(f"Columns: {info['columns']}", class_="badge bg-info me-2"),
            ui.tags.span(f"Missing: {missing_pct}%", class_="badge bg-warning me-2"),
            ui.tags.span(f"Memory: {mem_usage}", class_="badge bg-light text-dark"),
            class_="mb-1",
        )

    # -- Main content: two tabs with info icon --

    @render.ui
    def main_content():
        df = shared_store.raw_data()
        if df is None:
            return ui.div(
                ui.div(
                    ui.h5("No data loaded"),
                    ui.p("Select a data source from the sidebar and click Load Dataset to get started."),
                    class_="alert alert-info",
                ),
            )
        return ui.TagList(
            ui.div(
                ui.popover(
                    ui.tags.button(
                        "\u2139",
                        class_="btn btn-outline-secondary btn-sm rounded-circle",
                        style="width: 30px; height: 30px; padding: 0; font-size: 1.1rem; line-height: 1;",
                        type="button",
                    ),
                    ui.tags.h6("How to Use This Tab"),
                    ui.tags.hr(),
                    ui.tags.p(
                        ui.tags.strong("Data Table"),
                        " \u2014 Browse all rows and columns of your loaded dataset. "
                        "Use horizontal scrolling for wide datasets and pagination "
                        "at the bottom for navigation.",
                    ),
                    ui.tags.p(
                        ui.tags.strong("Filters"),
                        " \u2014 Click ",
                        ui.tags.em("+ Add Filter"),
                        " to narrow down rows. For text/categorical columns, pick one "
                        "or more values from a multi-select dropdown (including NA if "
                        "present). For numeric columns, set a min and/or max range. "
                        "Active filters appear as removable tags above the table.",
                    ),
                    ui.tags.p(
                        ui.tags.strong("Column Summary"),
                        " \u2014 View per-column statistics including data type, "
                        "missing values, quartiles, mean, standard deviation, and more.",
                    ),
                    ui.tags.p(
                        ui.tags.strong("Proceed"),
                        " \u2014 Click ",
                        ui.tags.em("Proceed to Data Cleaning"),
                        " at the bottom when you\u2019re ready for the next step.",
                    ),
                    title="Guide",
                    placement="left",
                ),
                class_="d-flex justify-content-end mb-0",
            ),
            ui.navset_card_tab(
                ui.nav_panel(
                    "Data Table",
                    ui.output_ui("filter_panel"),
                    ui.output_ui("filter_chips"),
                    ui.output_data_frame("data_table"),
                ),
                ui.nav_panel(
                    "Column Summary",
                    ui.output_data_frame("column_summary"),
                ),
            ),
        )

    # -- Filter panel UI --

    @render.ui
    def filter_panel():
        df = shared_store.raw_data()
        if df is None:
            return ui.TagList()

        if not show_filter_form():
            return ui.div(
                ui.input_action_button(
                    "add_filter_btn", "+ Add Filter",
                    class_="btn btn-outline-primary btn-sm",
                ),
                class_="mb-2",
            )

        columns = list(df.columns)
        return ui.div(
            ui.row(
                ui.column(
                    4,
                    ui.input_select(
                        "filter_col_select", "Column",
                        choices={"": "\u2014 select column \u2014", **{c: c for c in columns}},
                    ),
                ),
                ui.column(6, ui.output_ui("filter_value_control")),
                ui.column(
                    2,
                    ui.div(
                        ui.input_action_button(
                            "apply_filter_btn", "Apply",
                            class_="btn btn-primary btn-sm me-1",
                        ),
                        ui.input_action_button(
                            "cancel_filter_btn", "Cancel",
                            class_="btn btn-secondary btn-sm",
                        ),
                        class_="d-flex gap-1 mt-4",
                    ),
                ),
            ),
            class_="border rounded p-2 mb-2 bg-light",
        )

    @render.ui
    def filter_value_control():
        df = shared_store.raw_data()
        if df is None:
            return ui.TagList()

        try:
            col = input.filter_col_select()
        except Exception:
            return ui.p("Select a column first.", class_="text-muted small mt-4")
        if not col or col not in df.columns:
            return ui.p("Select a column first.", class_="text-muted small mt-4")

        series = df[col]
        if _is_categorical(series):
            unique_vals = sorted(series.dropna().unique().astype(str).tolist())
            choices: dict[str, str] = {v: v for v in unique_vals}
            if int(series.isnull().sum()) > 0:
                choices["(NA)"] = "(NA) \u2014 missing"
            return ui.input_selectize(
                "filter_cat_values", "Select values",
                choices=choices,
                multiple=True,
            )
        col_min = float(series.min()) if not pd.isna(series.min()) else 0
        col_max = float(series.max()) if not pd.isna(series.max()) else 0
        return ui.row(
            ui.column(
                6,
                ui.input_numeric(
                    "filter_num_min",
                    f"Min (\u2265 {col_min:g})",
                    value=None,
                ),
            ),
            ui.column(
                6,
                ui.input_numeric(
                    "filter_num_max",
                    f"Max (\u2264 {col_max:g})",
                    value=None,
                ),
            ),
        )

    # -- Filter chips --

    @render.ui
    def filter_chips():
        filters = active_filters()
        if not filters:
            return ui.TagList()

        remove_id = session.ns("remove_filter")
        chips = []
        for i, f in enumerate(filters):
            if f["type"] == "categorical":
                label = f"{f['column']}: {', '.join(f['values'])}"
            else:
                parts = []
                if f.get("min") is not None:
                    parts.append(f"\u2265 {f['min']}")
                if f.get("max") is not None:
                    parts.append(f"\u2264 {f['max']}")
                label = f"{f['column']}: {' & '.join(parts)}"

            chip = ui.tags.span(
                label, " ",
                ui.tags.button(
                    "\u00d7", type="button",
                    class_="btn-close btn-close-white ms-1",
                    style="font-size: 0.6rem;",
                    onclick=(
                        f"Shiny.setInputValue('{remove_id}', {i}, "
                        "{priority: 'event'})"
                    ),
                ),
                class_="badge bg-primary me-1 mb-1 d-inline-flex align-items-center",
                style="font-size: 0.85rem; padding: 0.4em 0.6em;",
            )
            chips.append(chip)

        fdf = filtered_df()
        raw = shared_store.raw_data()
        total = raw.shape[0] if raw is not None else 0
        shown = fdf.shape[0] if fdf is not None else 0

        return ui.div(
            ui.div(
                ui.tags.small("Active filters: ", class_="text-muted me-1"),
                *chips,
            ),
            ui.tags.small(
                f"Showing {shown:,} of {total:,} rows",
                class_="text-muted",
            ),
            class_="mb-2",
        )

    # -- DataGrid renders --

    @render.data_frame
    def data_table():
        df = filtered_df()
        if df is None:
            return pd.DataFrame()
        return render.DataGrid(df, height="100%")

    @render.data_frame
    def column_summary():
        df = shared_store.raw_data()
        if df is None:
            return pd.DataFrame()
        summary = _build_column_summary(df)
        return render.DataGrid(summary, height="100%")

    # -- Proceed button --

    @render.ui
    def next_step_btn():
        if shared_store.raw_data() is None:
            return ui.TagList()
        return ui.div(
            ui.input_action_button(
                "go_to_cleaning",
                "Proceed to Data Cleaning \u2192",
                class_="btn-success btn-lg mt-3",
            ),
            class_="d-flex justify-content-end",
        )

    @reactive.effect
    @reactive.event(input.go_to_cleaning)
    def _go_to_cleaning():
        target = app_session if app_session is not None else session
        ui.update_navs("main_nav", selected="Data Cleaning", session=target)

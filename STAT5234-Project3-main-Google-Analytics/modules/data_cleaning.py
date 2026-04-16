"""
Data Cleaning Module — Member 2

Reads: shared_store.raw_data
Writes: shared_store.cleaned_data
"""

from __future__ import annotations

import re

import matplotlib.pyplot as plt
import pandas as pd
from shiny import Inputs, Outputs, Session, module, reactive, render, ui
from sklearn.preprocessing import MinMaxScaler, StandardScaler


@module.ui
def data_cleaning_ui():
    return ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Cleaning Options"),
            ui.hr(),

            # Step 1: Missing-value standardization
            ui.h5("Step 1. Standardize Missing Values"),
            ui.p("Convert empty strings / NA-like tokens to true missing values."),
            ui.input_checkbox("strip_text_before_missing", "Trim whitespace before missing-value check", value=True),
            ui.input_checkbox_group(
                "missing_tokens",
                "Tokens to treat as missing",
                choices={
                    "": '"" (empty string)',
                    " ": '" " (single space)',
                    "NA": "NA",
                    "N/A": "N/A",
                    "na": "na",
                    "null": "null",
                    "NULL": "NULL",
                    "None": "None",
                    "?": "?",
                    "-": "-",
                },
                selected=["", " ", "NA", "N/A", "na", "null", "NULL", "None", "?", "-"],
            ),
            ui.input_action_button(
                "standardize_missing",
                "Apply Missing-Value Standardization",
                class_="btn-outline-primary w-100 mb-2",
            ),
            ui.hr(),

            # Step 2: Format standardization
            ui.h5("Step 2. Format Standardization"),
            ui.input_checkbox("standardize_colnames", "Standardize column names", value=True),
            ui.input_checkbox("trim_text", "Trim whitespace in text columns", value=True),
            ui.input_checkbox("lowercase_text", "Convert text columns to lowercase", value=False),
            ui.input_text(
                "strip_characters",
                "Strip characters from text columns",
                placeholder="e.g. $,% ",
            ),
            ui.input_checkbox("try_numeric_conversion", "Try converting text columns to numeric", value=True),
            ui.input_action_button(
                "apply_standardization",
                "Apply Format Standardization",
                class_="btn-outline-secondary w-100 mb-2",
            ),
            ui.hr(),

            # Step 3: Drop columns
            ui.h5("Step 3. Drop Columns"),
            ui.p("Remove unnecessary columns (e.g. IDs, constants).", class_="text-muted small"),
            ui.output_ui("drop_columns_selector"),
            ui.input_action_button(
                "apply_drop_columns",
                "Drop Selected Columns",
                class_="btn-outline-danger w-100 mb-2",
            ),
            ui.hr(),

            # Step 4: Handle missing values
            ui.h5("Step 4. Handle Missing Values"),
            ui.output_ui("missing_summary"),

            # 4a: Per-column override
            ui.tags.strong("4a. Per-Column Impute (optional)", class_="d-block mb-1"),
            ui.p("Handle special columns first before bulk impute.", class_="text-muted small"),
            ui.output_ui("per_col_impute_column_selector"),
            ui.output_ui("per_col_impute_method_ui"),
            ui.input_action_button(
                "apply_per_col_impute",
                "Apply to Selected Column",
                class_="btn-outline-info w-100 mb-2",
            ),

            # 4b: Bulk strategy
            ui.tags.strong("4b. Bulk Impute / Drop", class_="d-block mb-1"),
            ui.p("Apply to all remaining columns with missing values.", class_="text-muted small"),
            ui.input_select(
                "missing_strategy",
                "Missing-value strategy",
                choices={
                    "drop_rows": "Drop rows with any missing values",
                    "drop_cols_threshold": "Drop columns above missing threshold",
                    "impute_mean_median_mode": "Impute numeric + categorical columns",
                },
                selected="drop_rows",
            ),
            ui.output_ui("missing_strategy_options"),
            ui.input_action_button(
                "apply_missing",
                "Apply Bulk Handling",
                class_="btn-warning w-100 mb-2",
            ),
            ui.hr(),

            # Step 5: Duplicate handling
            ui.h5("Step 5. Handle Duplicate Rows"),
            ui.output_ui("duplicate_summary"),
            ui.input_action_button(
                "remove_duplicates",
                "Remove Exact Duplicate Rows",
                class_="btn-outline-danger w-100 mb-2",
            ),
            ui.hr(),

            # Step 6: Remap categorical values
            ui.h5("Step 6. Remap Categorical Values"),
            ui.p("Fix typos or merge similar labels.", class_="text-muted small"),
            ui.output_ui("remap_column_selector"),
            ui.output_ui("remap_value_selector"),
            ui.input_text(
                "remap_target_value",
                "Replace selected values with:",
                placeholder="correct value",
            ),
            ui.input_action_button(
                "apply_remap",
                "Apply Remap",
                class_="btn-outline-secondary w-100 mb-2",
            ),
            ui.hr(),

            # Step 7: Change column types
            ui.h5("Step 7. Change Column Types"),
            ui.p("Convert columns to the correct data type.", class_="text-muted small"),
            ui.output_ui("dtype_column_selector"),
            ui.output_ui("dtype_current_display"),
            ui.input_select(
                "dtype_target",
                "Convert to",
                choices={
                    "numeric": "Numeric",
                    "boolean": "Boolean",
                    "categorical": "Categorical",
                    "text": "Text (object)",
                },
            ),
            ui.output_ui("dtype_boolean_options"),
            ui.input_action_button(
                "apply_dtype_change",
                "Apply Type Change",
                class_="btn-outline-secondary w-100 mb-2",
            ),
            ui.hr(),

            # Step 8: Outlier handling
            ui.h5("Step 8. Handle Outliers"),
            ui.input_select(
                "outlier_method",
                "Outlier method",
                choices={
                    "none": "None",
                    "iqr_remove": "IQR: Remove rows",
                    "iqr_cap": "IQR: Cap values",
                    "zscore_remove": "Z-score: Remove rows",
                    "zscore_cap": "Z-score: Cap values",
                    "percentile_cap": "Percentile: Cap values",
                },
                selected="none",
            ),
            ui.output_ui("outlier_options_ui"),
            ui.input_action_button(
                "apply_outliers",
                "Apply Outlier Handling",
                class_="btn-outline-danger w-100 mb-2",
            ),
            ui.hr(),

            # Step 9: Scaling
            ui.h5("Step 9. Scale Numeric Features"),
            ui.input_select(
                "scaling_method",
                "Scaling method",
                choices={
                    "none": "None",
                    "standard": "StandardScaler",
                    "minmax": "MinMaxScaler",
                },
                selected="none",
            ),
            ui.output_ui("scaling_exclude_ui"),
            ui.input_action_button(
                "apply_scaling",
                "Apply Scaling",
                class_="btn-outline-primary w-100 mb-2",
            ),
            ui.hr(),

            # Step 10: Encoding
            ui.h5("Step 10. Encode Categorical Features"),
            ui.input_select(
                "encoding_method",
                "Encoding method",
                choices={
                    "none": "None",
                    "onehot": "One-Hot Encoding",
                    "label": "Label Encoding",
                },
                selected="none",
            ),
            ui.input_checkbox(
                "onehot_drop_first",
                "Drop first category (avoid multicollinearity)",
                value=False,
            ),
            ui.input_action_button(
                "apply_encoding",
                "Apply Encoding",
                class_="btn-outline-primary w-100 mb-2",
            ),
            ui.hr(),

            # Final save
            ui.input_action_button("apply_cleaning", "Apply & Save", class_="btn-primary w-100"),
            width=360,
        ),

        # Main panel
        ui.output_ui("guard_message"),
        ui.output_ui("quality_overview"),

        ui.navset_card_tab(
            ui.nav_panel(
                "Preview",
                ui.output_data_frame("cleaning_preview"),
            ),
            ui.nav_panel(
                "Missing Values",
                ui.output_plot("missing_plot"),
                ui.output_data_frame("missing_table"),
            ),
            ui.nav_panel(
                "Distributions",
                ui.input_select("dist_col", "Select numeric column", choices=[]),
                ui.output_plot("distribution_plot"),
            ),
            ui.nav_panel(
                "Outliers",
                ui.input_select("outlier_col", "Select numeric column", choices=[]),
                ui.output_plot("outlier_plot"),
            ),
            ui.nav_panel(
                "Info",
                ui.output_data_frame("column_info"),
            ),
        ),
        ui.div(
            ui.input_action_button(
                "undo_btn",
                "↩ Undo Last Step",
                class_="btn-outline-warning",
            ),
            class_="d-flex justify-content-start mt-2",
        ),
        ui.output_ui("next_step_btn"),
        fillable=True,
    )


@module.server
def data_cleaning_server(input: Inputs, output: Outputs, session: Session, shared_store, app_session=None, group_label=None,):

    # =========================================================================
    # PREREQUISITE GUARD (DO NOT MODIFY)
    # =========================================================================
    @render.ui
    def guard_message():
        if shared_store.raw_data() is None:
            return ui.div(
                ui.div(
                    ui.h4("No data available"),
                    ui.p("Please go to the Data Loading tab and upload or select a dataset first."),
                    class_="alert alert-warning",
                ),
            )
        return ui.TagList()
    # =========================================================================

    working_copy: reactive.value[pd.DataFrame | None] = reactive.value(None)
    undo_history: reactive.value[list] = reactive.value([])

    def emit_ga(event_name: str, extra_params: dict | None = None):
        target_session = app_session if app_session is not None else session
        params = {
            "group": group_label,
            "tab_name": "Data Cleaning",
        }
        if extra_params:
            params.update(extra_params)

        target_session.send_custom_message(
            "ga_event",
            {
                "event_name": event_name,
                "params": params,
            },
        )
    def _push_history(df: pd.DataFrame):
        """Save current state before a cleaning step modifies it."""
        stack = undo_history().copy()
        stack.append(df.copy())
        # Keep at most 20 snapshots to limit memory usage
        if len(stack) > 20:
            stack = stack[-20:]
        undo_history.set(stack)

    # -------------------------------------------------------------------------
    # Helper functions
    # -------------------------------------------------------------------------
    def _get_numeric_cols(df: pd.DataFrame) -> list[str]:
        return df.select_dtypes(include="number").columns.tolist()

    def _get_categorical_cols(df: pd.DataFrame) -> list[str]:
        return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    def _standardize_col_name(name: str) -> str:
        name = str(name).strip().lower()
        name = re.sub(r"\s+", "_", name)
        name = re.sub(r"[^a-z0-9_]", "", name)
        name = re.sub(r"_+", "_", name)
        return name.strip("_")

    # -------------------------------------------------------------------------
    # Sync working copy with raw data
    # -------------------------------------------------------------------------
    @reactive.effect
    def _sync_raw():
        df = shared_store.raw_data()
        if df is not None:
            working_copy.set(df.copy())
            undo_history.set([])

    @reactive.effect
    @reactive.event(input.undo_btn)
    def _undo():
        stack = undo_history().copy()
        if not stack:
            ui.notification_show("Nothing to undo.", type="warning")
            return
        prev = stack.pop()
        undo_history.set(stack)
        working_copy.set(prev)
        ui.notification_show(f"Undo successful. ({len(stack)} step(s) remaining)", type="message")

    # -------------------------------------------------------------------------
    # Update dynamic select inputs for plots
    # -------------------------------------------------------------------------
    @reactive.effect
    def _update_numeric_selects():
        df = working_copy()
        if df is None:
            ui.update_select("dist_col", choices={}, session=session)
            ui.update_select("outlier_col", choices={}, session=session)
            return

        numeric_cols = _get_numeric_cols(df)
        choices = {col: col for col in numeric_cols}
        selected = numeric_cols[0] if numeric_cols else None

        ui.update_select("dist_col", choices=choices, selected=selected, session=session)
        ui.update_select("outlier_col", choices=choices, selected=selected, session=session)

    # -------------------------------------------------------------------------
    # Conditional controls for missing-value strategy
    # -------------------------------------------------------------------------
    @render.ui
    def missing_strategy_options():
        strategy = input.missing_strategy()
        if strategy == "drop_cols_threshold":
            return ui.input_slider(
                "missing_threshold",
                "Column missing threshold (%)",
                min=0,
                max=100,
                value=50,
                step=5,
            )
        if strategy == "impute_mean_median_mode":
            return ui.TagList(
                ui.input_select(
                    "numeric_impute",
                    "Numeric imputation",
                    choices={"mean": "Mean", "median": "Median", "mode": "Mode"},
                    selected="median",
                ),
                ui.input_select(
                    "categorical_impute",
                    "Categorical imputation",
                    choices={"mode": "Mode", "unknown": 'Fill with "Unknown"'},
                    selected="mode",
                ),
            )
        return ui.TagList()

    # =========================================================================
    # Step 1: Standardize missing-value representation
    # =========================================================================
    @reactive.effect
    @reactive.event(input.standardize_missing)
    def _standardize_missing():
        df = working_copy()
        if df is None:
            return
        _push_history(df)

        df = df.copy()
        selected_tokens = input.missing_tokens()

        for col in df.columns:
            if df[col].dtype == "object" or str(df[col].dtype) == "category":
                df[col] = df[col].astype("object")

                if input.strip_text_before_missing():
                    df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

                df[col] = df[col].replace(selected_tokens, pd.NA)

        working_copy.set(df)
        emit_ga("missing_standardized_success")
        ui.notification_show("Step 1 done: standardized missing-value tokens.", type="message")

    # =========================================================================
    # Step 4a: Per-column impute
    # =========================================================================
    @render.ui
    def per_col_impute_column_selector():
        df = working_copy()
        if df is None:
            return ui.p("No data available.", class_="text-muted")
        missing_cols = [c for c in df.columns if df[c].isna().any()]
        if not missing_cols:
            return ui.p("No columns with missing values.", class_="text-success")
        labels = {c: f"{c} ({int(df[c].isna().sum())} missing)" for c in missing_cols}
        return ui.input_select("per_col_impute_col", "Column", choices=labels)

    @render.ui
    def per_col_impute_method_ui():
        df = working_copy()
        if df is None:
            return ui.TagList()
        try:
            col = input.per_col_impute_col()
        except Exception:
            return ui.TagList()
        if not col or col not in df.columns:
            return ui.TagList()

        is_numeric = pd.api.types.is_numeric_dtype(df[col])
        if is_numeric:
            choices = {
                "mean": "Mean",
                "median": "Median",
                "zero": "Fill with 0",
                "constant": "Fill with constant",
                "ffill": "Forward fill",
                "bfill": "Backward fill",
            }
        else:
            choices = {
                "mode": "Mode",
                "unknown": 'Fill with "Unknown"',
                "constant": "Fill with constant",
            }
        return ui.TagList(
            ui.input_select("per_col_method", "Method", choices=choices),
            ui.output_ui("per_col_constant_input"),
        )

    @render.ui
    def per_col_constant_input():
        try:
            method = input.per_col_method()
        except Exception:
            return ui.TagList()
        if method != "constant":
            return ui.TagList()
        return ui.input_text("per_col_constant_value", "Constant value", placeholder="enter value")

    @reactive.effect
    @reactive.event(input.apply_per_col_impute)
    def _apply_per_col_impute():
        df = working_copy()
        if df is None:
            return
        _push_history(df)

        try:
            col = input.per_col_impute_col()
            method = input.per_col_method()
        except Exception:
            ui.notification_show("Please select a column and method.", type="warning")
            return

        if not col or col not in df.columns:
            ui.notification_show("Please select a valid column.", type="warning")
            return

        if not df[col].isna().any():
            ui.notification_show(f"'{col}' has no missing values.", type="warning")
            return

        df = df.copy()
        filled = int(df[col].isna().sum())

        if method == "mean":
            df[col] = df[col].fillna(df[col].mean())
        elif method == "median":
            df[col] = df[col].fillna(df[col].median())
        elif method == "zero":
            df[col] = df[col].fillna(0)
        elif method == "ffill":
            df[col] = df[col].ffill()
        elif method == "bfill":
            df[col] = df[col].bfill()
        elif method == "mode":
            mode_series = df[col].mode(dropna=True)
            fill_value = mode_series.iloc[0] if not mode_series.empty else "Unknown"
            df[col] = df[col].fillna(fill_value)
        elif method == "unknown":
            df[col] = df[col].fillna("Unknown")
        elif method == "constant":
            try:
                const = input.per_col_constant_value().strip()
            except Exception:
                const = ""
            if not const:
                ui.notification_show("Please enter a constant value.", type="warning")
                return
            if pd.api.types.is_numeric_dtype(df[col]):
                try:
                    const = float(const)
                except ValueError:
                    ui.notification_show("Please enter a valid number.", type="warning")
                    return
            df[col] = df[col].fillna(const)

        remaining = int(df[col].isna().sum())
        working_copy.set(df)
        ui.notification_show(
            f"Step 4a done: filled {filled - remaining} missing values in '{col}' using {method}.",
            type="message",
        )

    # =========================================================================
    # Step 4b: Bulk handle missing values
    # =========================================================================
    @reactive.effect
    @reactive.event(input.apply_missing)
    def _apply_missing():
        df = working_copy()
        if df is None:
            return
        _push_history(df)

        df = df.copy()
        strategy = input.missing_strategy()
        before_rows = len(df)
        before_cols = len(df.columns)

        if strategy == "drop_rows":
            df = df.dropna().reset_index(drop=True)
            msg = f"Dropped {before_rows - len(df)} rows with missing values."

        elif strategy == "drop_cols_threshold":
            threshold = input.missing_threshold() / 100.0
            missing_ratio = df.isna().mean()
            cols_to_keep = missing_ratio[missing_ratio <= threshold].index.tolist()
            df = df[cols_to_keep].copy()
            msg = f"Dropped {before_cols - len(df.columns)} columns above {input.missing_threshold()}% threshold."

        elif strategy == "impute_mean_median_mode":
            numeric_cols = _get_numeric_cols(df)
            categorical_cols = _get_categorical_cols(df)

            for col in numeric_cols:
                if df[col].isna().any():
                    num_method = input.numeric_impute()
                    if num_method == "mean":
                        fill_value = df[col].mean()
                    elif num_method == "mode":
                        mode_series = df[col].mode(dropna=True)
                        fill_value = mode_series.iloc[0] if not mode_series.empty else df[col].median()
                    else:
                        fill_value = df[col].median()
                    df[col] = df[col].fillna(fill_value)

            for col in categorical_cols:
                if df[col].isna().any():
                    if input.categorical_impute() == "mode":
                        mode_series = df[col].mode(dropna=True)
                        fill_value = mode_series.iloc[0] if not mode_series.empty else "Unknown"
                    else:
                        fill_value = "Unknown"
                    df[col] = df[col].fillna(fill_value)
            msg = f"Imputed missing values ({input.numeric_impute()} for numeric, {input.categorical_impute()} for categorical)."
        else:
            msg = "Missing values handled."

        working_copy.set(df)
        ui.notification_show(f"Step 4 done: {msg}", type="message")

    # =========================================================================
    # Step 5: Handle duplicates
    # =========================================================================
    @reactive.effect
    @reactive.event(input.remove_duplicates)
    def _remove_duplicates():
        df = working_copy()
        if df is None:
            return
        _push_history(df)
        before = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        removed = before - len(df)
        working_copy.set(df)
        emit_ga(
            "remove_duplicates_success",
            {
                "removed_rows": int(removed),
            },
        )
        ui.notification_show(f"Step 5 done: removed {removed} duplicate rows.", type="message")

    # =========================================================================
    # Step 2: Format standardization
    # =========================================================================
    @reactive.effect
    @reactive.event(input.apply_standardization)
    def _apply_standardization():
        df = working_copy()
        if df is None:
            return
        _push_history(df)

        df = df.copy()

        if input.standardize_colnames():
            df.columns = [_standardize_col_name(col) for col in df.columns]

        text_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        for col in text_cols:
            df[col] = df[col].astype("object")

            if input.trim_text():
                df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

            if input.lowercase_text():
                df[col] = df[col].apply(lambda x: x.lower() if isinstance(x, str) else x)

        chars_to_strip = input.strip_characters().strip()
        if chars_to_strip:
            text_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
            for col in text_cols:
                df[col] = df[col].apply(
                    lambda x, ch=chars_to_strip: "".join(c for c in x if c not in ch) if isinstance(x, str) else x
                )

        if input.try_numeric_conversion():
            object_cols = df.select_dtypes(include=["object"]).columns.tolist()
            for col in object_cols:
                converted = pd.to_numeric(df[col], errors="coerce")
                non_missing_original = df[col].notna().sum()
                non_missing_converted = converted.notna().sum()
                if non_missing_original > 0 and non_missing_converted == non_missing_original:
                    df[col] = converted

        working_copy.set(df)
        ui.notification_show("Step 2 done: standardized formats.", type="message")

    # =========================================================================
    # Step 3: Drop columns
    # =========================================================================
    @render.ui
    def drop_columns_selector():
        df = working_copy()
        if df is None:
            return ui.p("No data available.", class_="text-muted")
        all_cols = df.columns.tolist()
        return ui.input_selectize(
            "columns_to_drop",
            "Select columns to drop",
            choices=all_cols,
            multiple=True,
        )

    @reactive.effect
    @reactive.event(input.apply_drop_columns)
    def _apply_drop_columns():
        df = working_copy()
        if df is None:
            return
        _push_history(df)

        try:
            cols_to_drop = list(input.columns_to_drop())
        except Exception:
            cols_to_drop = []

        if not cols_to_drop:
            ui.notification_show("Please select at least one column to drop.", type="warning")
            return

        df = df.drop(columns=cols_to_drop, errors="ignore")
        working_copy.set(df)
        emit_ga(
            "drop_columns_success",
            {
                "dropped_count": len(cols_to_drop),
            },
        )
        ui.notification_show(
            f"Step 3 done: dropped {len(cols_to_drop)} column(s): {', '.join(cols_to_drop)}.",
            type="message",
        )

    # =========================================================================
    # Step 6: Remap categorical values
    # =========================================================================
    remap_col_choices: reactive.value[list[str]] = reactive.value([])

    @reactive.effect
    def _update_remap_columns():
        df = working_copy()
        if df is None:
            remap_col_choices.set([])
            return
        remap_col_choices.set(_get_categorical_cols(df))

    @render.ui
    def remap_column_selector():
        cat_cols = remap_col_choices()
        if not cat_cols:
            return ui.p("No categorical columns found.", class_="text-warning")
        return ui.input_select("remap_column", "Select column", choices=cat_cols)

    @render.ui
    def remap_value_selector():
        df = working_copy()
        if df is None:
            return ui.TagList()
        try:
            col = input.remap_column()
        except Exception:
            return ui.TagList()
        if not col or col not in df.columns:
            return ui.TagList()

        counts = df[col].value_counts(dropna=False).reset_index()
        counts.columns = ["value", "count"]
        counts["value"] = counts["value"].astype(str)

        choices = {row["value"]: f"{row['value']} ({row['count']})" for _, row in counts.iterrows()}
        return ui.input_select(
            "remap_dirty_value",
            "Select value to replace",
            choices=choices,
        )

    @reactive.effect
    @reactive.event(input.apply_remap)
    def _apply_remap():
        df = working_copy()
        if df is None:
            return
        _push_history(df)

        try:
            col = input.remap_column()
            dirty_value = input.remap_dirty_value()
        except Exception:
            ui.notification_show("Please select a column and a value to remap.", type="warning")
            return

        target = input.remap_target_value().strip()
        if not target:
            ui.notification_show("Please enter the replacement value.", type="warning")
            return
        if dirty_value == target:
            ui.notification_show("The selected value is already the target value.", type="warning")
            return

        df = df.copy()
        if dirty_value == "nan":
            mask = df[col].isna()
        else:
            mask = df[col].astype(str) == dirty_value
        replaced_count = int(mask.sum())

        df.loc[mask, col] = target
        working_copy.set(df)
        ui.update_text("remap_target_value", value="", session=session)
        ui.notification_show(
            f"Step 6 done: replaced {replaced_count} values in '{col}' with '{target}'.",
            type="message",
        )

    # =========================================================================
    # Step 7: Change column types
    # =========================================================================
    @render.ui
    def dtype_column_selector():
        df = working_copy()
        if df is None:
            return ui.p("No data available.", class_="text-muted")
        all_cols = df.columns.tolist()
        return ui.input_select("dtype_column", "Select column", choices=all_cols)

    @render.ui
    def dtype_current_display():
        df = working_copy()
        if df is None:
            return ui.TagList()
        try:
            col = input.dtype_column()
        except Exception:
            return ui.TagList()
        if not col or col not in df.columns:
            return ui.TagList()
        current_dtype = str(df[col].dtype)
        n_unique = int(df[col].nunique(dropna=True))
        sample_vals = df[col].dropna().unique()[:5].tolist()
        sample_str = ", ".join(str(v) for v in sample_vals)
        return ui.div(
            ui.p(f"Current type: {current_dtype}", class_="mb-0 small"),
            ui.p(f"Unique values: {n_unique}", class_="mb-0 small"),
            ui.p(f"Sample: {sample_str}", class_="mb-0 small text-muted"),
            class_="border rounded p-2 mb-2 bg-light",
        )

    @render.ui
    def dtype_boolean_options():
        try:
            target = input.dtype_target()
            col = input.dtype_column()
        except Exception:
            return ui.TagList()
        if target != "boolean":
            return ui.TagList()
        df = working_copy()
        if df is None or col not in df.columns:
            return ui.TagList()
        unique_vals = sorted(df[col].dropna().astype(str).unique().tolist())
        choices = {v: v for v in unique_vals}
        return ui.input_selectize(
            "dtype_true_values",
            "Select values that mean True",
            choices=choices,
            multiple=True,
        )

    @reactive.effect
    @reactive.event(input.apply_dtype_change)
    def _apply_dtype_change():
        df = working_copy()
        if df is None:
            return
        _push_history(df)

        try:
            col = input.dtype_column()
            target = input.dtype_target()
        except Exception:
            ui.notification_show("Please select a column and target type.", type="warning")
            return

        if not col or col not in df.columns:
            ui.notification_show("Please select a valid column.", type="warning")
            return

        df = df.copy()

        if target == "numeric":
            # Strip common formatting characters then convert
            stripped = df[col].apply(
                lambda x: x.replace("$", "").replace(",", "").strip() if isinstance(x, str) else x
            )
            converted = pd.to_numeric(stripped, errors="coerce")
            success = int(converted.notna().sum())
            total = int(df[col].notna().sum())
            df[col] = converted
            working_copy.set(df)
            ui.notification_show(
                f"Step 7 done: converted '{col}' to numeric ({success}/{total} values parsed).",
                type="message",
            )

        elif target == "boolean":
            try:
                true_values = list(input.dtype_true_values())
            except Exception:
                true_values = []
            if not true_values:
                ui.notification_show("Please select which values mean True.", type="warning")
                return
            original_na = df[col].isna()
            str_col = df[col].astype(str)
            bool_series = str_col.isin(true_values).astype("boolean")
            bool_series[original_na] = pd.NA
            df[col] = bool_series
            working_copy.set(df)
            ui.notification_show(
                f"Step 7 done: converted '{col}' to boolean (True values: {', '.join(true_values)}).",
                type="message",
            )

        elif target == "categorical":
            df[col] = df[col].astype("category")
            working_copy.set(df)
            ui.notification_show(
                f"Step 7 done: converted '{col}' to categorical.",
                type="message",
            )

        elif target == "text":
            df[col] = df[col].astype(str).replace("nan", pd.NA)
            working_copy.set(df)
            ui.notification_show(
                f"Step 7 done: converted '{col}' to text.",
                type="message",
            )

    # =========================================================================
    # Step 9: Scale numeric features
    # =========================================================================
    @render.ui
    def scaling_exclude_ui():
        df = working_copy()
        if df is None:
            return ui.TagList()
        num_cols = _get_numeric_cols(df)
        if not num_cols:
            return ui.TagList()
        return ui.input_selectize(
            "scaling_exclude_cols",
            "Exclude columns (e.g. target/label)",
            choices=num_cols,
            multiple=True,
        )

    @reactive.effect
    @reactive.event(input.apply_scaling)
    def _apply_scaling():
        df = working_copy()
        if df is None:
            return

        method = input.scaling_method()
        if method == "none":
            ui.notification_show("Step 9 skipped: no scaling method selected.", type="warning")
            return

        _push_history(df)
        df = df.copy()
        numeric_cols = _get_numeric_cols(df)

        if not numeric_cols:
            ui.notification_show("Step 9 skipped: no numeric columns available.", type="warning")
            return

        try:
            exclude = list(input.scaling_exclude_cols())
        except Exception:
            exclude = []

        cols_to_scale = [col for col in numeric_cols if col not in exclude and not df[col].isna().any()]
        if not cols_to_scale:
            ui.notification_show("Step 9 skipped: all numeric columns have missing values or excluded.", type="warning")
            return

        if method == "standard":
            scaler = StandardScaler()
        else:
            scaler = MinMaxScaler()

        df[cols_to_scale] = scaler.fit_transform(df[cols_to_scale])
        working_copy.set(df)
        emit_ga(
            "scaling_applied_success",
            {
                "method": method,
                "scaled_columns": len(cols_to_scale),
            },
        )
        ui.notification_show(f"Step 9 done: applied {method} scaling to {len(cols_to_scale)} columns.", type="message")

    # =========================================================================
    # Step 10: Encode categorical features
    # =========================================================================
    @reactive.effect
    @reactive.event(input.apply_encoding)
    def _apply_encoding():
        df = working_copy()
        if df is None:
            return

        method = input.encoding_method()
        if method == "none":
            ui.notification_show("Step 10 skipped: no encoding method selected.", type="warning")
            return

        _push_history(df)

        df = df.copy()
        # Exclude bool/boolean columns — they are already binary
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        if not cat_cols:
            ui.notification_show("Step 10 skipped: no categorical columns found.", type="warning")
            return

        if method == "onehot":
            df = pd.get_dummies(df, columns=cat_cols, drop_first=input.onehot_drop_first())
        elif method == "label":
            for col in cat_cols:
                df[col] = df[col].astype("category").cat.codes

        working_copy.set(df)
        emit_ga(
            "encoding_applied_success",
            {
                "method": method,
                "encoded_columns": len(cat_cols),
            },
        )
        ui.notification_show(f"Step 10 done: applied {method} encoding to {len(cat_cols)} columns.", type="message")

    # =========================================================================
    # Step 8: Handle outliers
    # =========================================================================
    @render.ui
    def outlier_options_ui():
        try:
            method = input.outlier_method()
        except Exception:
            return ui.TagList()
        if method in ("zscore_remove", "zscore_cap"):
            return ui.input_numeric(
                "zscore_threshold",
                "Z-score threshold",
                value=3,
                min=1,
                max=10,
                step=0.5,
            )
        if method == "percentile_cap":
            return ui.input_slider(
                "percentile_cutoff",
                "Percentile cutoff (%)",
                min=1,
                max=10,
                value=1,
                step=1,
                post="%",
            )
        return ui.TagList()

    @reactive.effect
    @reactive.event(input.apply_outliers)
    def _apply_outliers():
        df = working_copy()
        if df is None:
            return

        method = input.outlier_method()
        if method == "none":
            ui.notification_show("Step 8 skipped: no outlier method selected.", type="warning")
            return

        numeric_cols = _get_numeric_cols(df)
        if not numeric_cols:
            ui.notification_show("Step 8 skipped: no numeric columns available.", type="warning")
            return

        _push_history(df)
        df = df.copy()

        before_rows = len(df)

        if method == "iqr_remove":
            keep_mask = pd.Series([True] * len(df), index=df.index)

            for col in numeric_cols:
                series = df[col].dropna()
                if series.empty:
                    continue
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr == 0:
                    continue
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                col_mask = df[col].isna() | ((df[col] >= lower) & (df[col] <= upper))
                keep_mask = keep_mask & col_mask

            df = df.loc[keep_mask].reset_index(drop=True)
            removed = before_rows - len(df)
            working_copy.set(df)
            ui.notification_show(f"Step 8 done: removed {removed} outlier rows (IQR).", type="message")

        elif method == "iqr_cap":
            for col in numeric_cols:
                series = df[col].dropna()
                if series.empty:
                    continue
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr == 0:
                    continue
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                df[col] = df[col].clip(lower=lower, upper=upper)

            working_copy.set(df)
            ui.notification_show("Step 8 done: capped outlier values (IQR).", type="message")

        elif method == "zscore_remove":
            threshold = input.zscore_threshold() or 3
            keep_mask = pd.Series([True] * len(df), index=df.index)

            for col in numeric_cols:
                series = df[col].dropna()
                if series.empty or series.std() == 0:
                    continue
                z = (df[col] - series.mean()) / series.std()
                col_mask = df[col].isna() | (z.abs() <= threshold)
                keep_mask = keep_mask & col_mask

            df = df.loc[keep_mask].reset_index(drop=True)
            removed = before_rows - len(df)
            working_copy.set(df)
            ui.notification_show(f"Step 8 done: removed {removed} outlier rows (Z-score > {threshold}).", type="message")

        elif method == "zscore_cap":
            threshold = input.zscore_threshold() or 3

            for col in numeric_cols:
                series = df[col].dropna()
                if series.empty or series.std() == 0:
                    continue
                mean = series.mean()
                std = series.std()
                lower = mean - threshold * std
                upper = mean + threshold * std
                df[col] = df[col].clip(lower=lower, upper=upper)

            working_copy.set(df)
            ui.notification_show(f"Step 8 done: capped outlier values (Z-score > {threshold}).", type="message")

        elif method == "percentile_cap":
            cutoff = input.percentile_cutoff() or 1
            lower_pct = cutoff / 100.0
            upper_pct = 1 - lower_pct

            for col in numeric_cols:
                series = df[col].dropna()
                if series.empty:
                    continue
                lower = series.quantile(lower_pct)
                upper = series.quantile(upper_pct)
                df[col] = df[col].clip(lower=lower, upper=upper)

            working_copy.set(df)
            ui.notification_show(f"Step 8 done: capped values at {cutoff}th / {100 - cutoff}th percentile.", type="message")

    # =========================================================================
    # Final save
    # =========================================================================
    @reactive.effect
    @reactive.event(input.apply_cleaning)
    def _apply():
        df = working_copy()
        if df is not None:
            shared_store.cleaned_data.set(df.copy())

            emit_ga(
                "cleaning_applied_success",
                {
                    "rows": int(df.shape[0]),
                    "columns": int(df.shape[1]),
                    "missing_cells": int(df.isna().sum().sum()),
                    "duplicate_rows": int(df.duplicated().sum()),
                },
            )

            ui.notification_show(
                f"Cleaned data saved: {df.shape[0]} rows, {df.shape[1]} columns.",
                type="message",
            )

    # =========================================================================
    # Summaries / tables
    # =========================================================================
    @render.ui
    def missing_summary():
        df = working_copy()
        if df is None:
            return ui.p("\u2014", class_="text-muted")

        missing = df.isnull().sum()
        total = int(missing.sum())

        if total == 0:
            return ui.p("No missing values detected.", class_="text-success")

        items = [
            ui.tags.li(f"{col}: {cnt} missing ({df[col].isna().mean():.1%})")
            for col, cnt in missing.items()
            if cnt > 0
        ]
        return ui.div(
            ui.p(f"Total missing cells: {total}", class_="text-danger"),
            ui.tags.ul(items),
        )

    @render.ui
    def duplicate_summary():
        df = working_copy()
        if df is None:
            return ui.p("\u2014", class_="text-muted")

        dup_count = int(df.duplicated().sum())
        dup_pct = dup_count / len(df) if len(df) > 0 else 0

        if dup_count == 0:
            return ui.p("No duplicate rows detected.", class_="text-success")

        return ui.div(
            ui.p(f"Duplicate rows: {dup_count}", class_="text-danger"),
            ui.p(f"Duplicate percentage: {dup_pct:.1%}", class_="text-danger"),
        )

    @render.ui
    def quality_overview():
        df = working_copy()
        if df is None:
            return ui.TagList()

        n_rows, n_cols = df.shape
        missing_cells = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())
        numeric_cols = len(_get_numeric_cols(df))
        categorical_cols = len(_get_categorical_cols(df))

        return ui.div(
            ui.div(
                ui.tags.span(f"Rows: {n_rows}", class_="badge bg-primary me-2"),
                ui.tags.span(f"Columns: {n_cols}", class_="badge bg-primary me-2"),
                ui.tags.span(f"Missing cells: {missing_cells}", class_="badge bg-warning text-dark me-2"),
                ui.tags.span(f"Duplicate rows: {duplicate_rows}", class_="badge bg-danger me-2"),
                ui.tags.span(f"Numeric cols: {numeric_cols}", class_="badge bg-info me-2"),
                ui.tags.span(f"Categorical cols: {categorical_cols}", class_="badge bg-secondary me-2"),
                class_="mb-1",
            ),
        )

    @render.data_frame
    def cleaning_preview():
        df = working_copy()
        if df is None:
            return pd.DataFrame()
        return render.DataGrid(df, height="100%")

    @render.data_frame
    def missing_table():
        df = working_copy()
        if df is None:
            return pd.DataFrame()

        summary = pd.DataFrame({
            "Column": df.columns,
            "Dtype": [str(df[col].dtype) for col in df.columns],
            "Missing Count": [int(df[col].isna().sum()) for col in df.columns],
            "Missing %": [round(float(df[col].isna().mean() * 100), 2) for col in df.columns],
        })
        return render.DataGrid(summary, height="100%")

    @render.data_frame
    def column_info():
        df = working_copy()
        if df is None:
            return pd.DataFrame()

        info_df = pd.DataFrame({
            "Column": df.columns,
            "Dtype": [str(df[col].dtype) for col in df.columns],
            "Non-Null": [int(df[col].notna().sum()) for col in df.columns],
            "Missing": [int(df[col].isna().sum()) for col in df.columns],
            "Unique": [int(df[col].nunique(dropna=True)) for col in df.columns],
        })
        return render.DataGrid(info_df, height="100%")

    # =========================================================================
    # Plots
    # =========================================================================
    @render.plot
    def missing_plot():
        df = working_copy()
        fig, ax = plt.subplots(figsize=(8, 4))

        if df is None:
            ax.text(0.5, 0.5, "No data loaded", ha="center", va="center")
            ax.axis("off")
            return fig

        missing_counts = df.isna().sum()
        missing_counts = missing_counts[missing_counts > 0]

        if missing_counts.empty:
            ax.text(0.5, 0.5, "No missing values detected", ha="center", va="center")
            ax.axis("off")
            return fig

        missing_counts.sort_values(ascending=False).plot(kind="bar", ax=ax)
        ax.set_title("Missing Values by Column")
        ax.set_xlabel("Column")
        ax.set_ylabel("Missing Count")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        return fig

    @render.plot
    def distribution_plot():
        df = working_copy()
        fig, ax = plt.subplots(figsize=(8, 4))

        if df is None:
            ax.text(0.5, 0.5, "No data loaded", ha="center", va="center")
            ax.axis("off")
            return fig

        col = input.dist_col()
        if not col or col not in df.columns:
            ax.text(0.5, 0.5, "No numeric column selected", ha="center", va="center")
            ax.axis("off")
            return fig

        series = df[col].dropna()
        if series.empty:
            ax.text(0.5, 0.5, "Selected column has no valid values", ha="center", va="center")
            ax.axis("off")
            return fig

        ax.hist(series, bins=20)
        ax.set_title(f"Distribution of {col}")
        ax.set_xlabel(col)
        ax.set_ylabel("Frequency")
        plt.tight_layout()
        return fig

    @render.plot
    def outlier_plot():
        df = working_copy()
        fig, ax = plt.subplots(figsize=(8, 4))

        if df is None:
            ax.text(0.5, 0.5, "No data loaded", ha="center", va="center")
            ax.axis("off")
            return fig

        col = input.outlier_col()
        if not col or col not in df.columns:
            ax.text(0.5, 0.5, "No numeric column selected", ha="center", va="center")
            ax.axis("off")
            return fig

        series = df[col].dropna()
        if series.empty:
            ax.text(0.5, 0.5, "Selected column has no valid values", ha="center", va="center")
            ax.axis("off")
            return fig

        ax.boxplot(series, vert=False)
        ax.set_title(f"Boxplot of {col}")
        ax.set_xlabel(col)
        plt.tight_layout()
        return fig

    # -- Proceed button --

    @render.ui
    def next_step_btn():
        if shared_store.cleaned_data() is None:
            return ui.TagList()
        return ui.div(
            ui.input_action_button(
                "go_to_feature_eng",
                "Proceed to Feature Engineering \u2192",
                class_="btn-success btn-lg mt-3",
            ),
            class_="d-flex justify-content-end",
        )

    @reactive.effect
    @reactive.event(input.go_to_feature_eng)
    def _go_to_feature_eng():
        emit_ga("proceed_to_feature_eng")
        target = app_session if app_session is not None else session
        ui.update_navs("main_nav", selected="Feature Engineering", session=target)

"""
Feature Engineering Module — Member 3

Reads: shared_store.cleaned_data
Writes: shared_store.engineered_data
"""


from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import Inputs, Outputs, Session, module, reactive, render, ui
from shinywidgets import output_widget, render_widget

# Help explanations shown in the sidebar; updates with the selected operation / transform.
_SINGLE_TRANSFORM_HELP: dict[str, str] = {
    "log": (
        "Natural logarithm ln(x). Compresses large values and reduces right skew. "
        "Requires positive values; non-positive values are clipped before logging."
    ),
    "log1p": (
        "Log1p: ln(1 + x). Use for nonnegative data that may include zeros (e.g. fares, counts). "
        "The +1 avoids ln(0)."
    ),
    "sqrt": (
        "Square root. Mildly reduces scale and helps with right-skewed nonnegative data; "
        "negative values are clipped to zero first."
    ),
    "square": (
        "Squares each value to emphasize large magnitudes and add nonlinearity. "
        "Can amplify outliers."
    ),
    "zscore": (
        "Z-score: subtract the column mean and divide by the standard deviation "
        "(on the current table). Not available if the column is constant (zero std)."
    ),
    "minmax": (
        "Min–max scaling to the [0, 1] interval using this column’s min and max. "
        "Not available if min equals max."
    ),
    "binning": (
        "Splits the numeric range into ordered intervals (bins), turning a continuous "
        "variable into categorical bins. Increase bins for finer granularity."
    ),
}

_COMBINE_HELP: dict[str, str] = {
    "add": (
        "Sum of two numeric columns. Useful for totals (e.g. combining counts into a size measure)."
    ),
    "multiply": (
        "Product of two columns. Captures joint magnitude when both values increase together."
    ),
    "ratio": (
        "First column divided by the second. Describes relative size; zeros in the denominator "
        "become missing (NaN)."
    ),
}

_DATETIME_PART_HELP: dict[str, str] = {
    "year": "Calendar year of each timestamp.",
    "month": "Month of year (1–12).",
    "day": "Day of month.",
    "dayofweek": "Weekday index: Monday=0 through Sunday=6.",
    "hour": "Hour of day (0–23).",
    "minute": "Minute within the hour (0–59).",
    "quarter": "Calendar quarter (1–4).",
    "is_weekend": "1 if Saturday or Sunday, else 0.",
    "dayofyear": "Day index within the year (1–366).",
}


@module.ui
def feature_engineering_ui():
    return ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Feature Engineering"),
            ui.hr(),

            ui.h5("Choose Operation Type"),
            ui.input_select(
                "operation_type",
                "Operation Category",
                choices={
                    "single": "Single-Column Transformation",
                    "combine": "Combine Two Columns",
                    "datetime": "Date / Time Extraction",
                },
            ),

            ui.output_ui("column_selector_ui"),
            ui.output_ui("operation_controls_ui"),
            ui.output_ui("transform_help"),

            ui.hr(),
            ui.input_text(
                "custom_feature_name",
                "Custom Feature Name (optional)",
                placeholder="Leave blank to auto-generate",
            ),

            ui.input_action_button(
                "apply_transform",
                "Apply",
                class_="btn-outline-primary w-100 mb-2",
            ),
            ui.input_action_button(
                "save_to_pipeline",
                "Save to Pipeline",
                class_="btn-primary w-100 mb-2",
            ),
            ui.input_action_button(
                "reset_features",
                "Reset to Cleaned Data",
                class_="btn-warning w-100",
            ),

            ui.hr(),
            ui.p(
                "Tip: Apply adds the feature to the working table. Save pushes it to the pipeline for EDA.",
                class_="text-muted",
                style="font-size: 0.9em;",
            ),
            ui.hr(),
            ui.h5("Feature History"),
            ui.output_ui("feature_history"),
            width=340,
        ),

        ui.output_ui("guard_message"),

        ui.navset_card_tab(
            ui.nav_panel(
                "Preview",
                ui.output_ui("status_message"),
                ui.div(
                    ui.div(
                        output_widget("before_plot"),
                        ui.br(),
                        output_widget("after_plot"),
                        style="flex: 1 1 0; min-width: 0;",
                    ),
                    ui.div(
                        ui.output_data_frame("transform_preview"),
                        style="flex: 0 0 auto; resize: horizontal; overflow: auto; min-width: 150px; max-width: 50%; border-left: 1px solid #dee2e6; padding-left: 8px;",
                    ),
                    style="display: flex; height: 100%; gap: 8px;",
                ),
            ),
            ui.nav_panel(
                "Current Data",
                ui.h4("Current Working Data"),
                ui.output_data_frame("current_data"),
            ),
        ),
        ui.div(
            ui.div(
                ui.input_action_button(
                    "undo_btn",
                    "↩ Undo Last Apply",
                    class_="btn-outline-warning",
                ),
            ),
            ui.div(
                ui.input_action_button(
                    "go_to_eda",
                    "Proceed to EDA →",
                    class_="btn-success btn-lg",
                ),
            ),
            class_="d-flex justify-content-between align-items-center mt-2",
        ),
    )


@module.server
def feature_engineering_server(input: Inputs, output: Outputs, session: Session, shared_store, app_session=None):

    # =========================================================================
    # === PREREQUISITE GUARD (DO NOT MODIFY) ===
    # =========================================================================
    @render.ui
    def guard_message():
        if shared_store.cleaned_data() is None:
            return ui.div(
                ui.div(
                    ui.h4("No cleaned data available"),
                    ui.p("Please go to the Data Cleaning tab and process your data first."),
                    class_="alert alert-warning",
                ),
            )
        return ui.TagList()
    # =========================================================================

    working_copy: reactive.value[pd.DataFrame | None] = reactive.value(None)
    feature_history_store: reactive.value[list[str]] = reactive.value([])
    status_store: reactive.value[str] = reactive.value("")
    undo_history: reactive.value[list] = reactive.value([])

    def _push_history(df: pd.DataFrame):
        """Save current state before an apply modifies it."""
        stack = undo_history().copy()
        stack.append(df.copy())
        if len(stack) > 20:
            stack = stack[-20:]
        undo_history.set(stack)

    @reactive.effect
    def _sync_cleaned():
        df = shared_store.cleaned_data()
        if df is not None:
            working_copy.set(df.copy())
            feature_history_store.set([])
            undo_history.set([])
            shared_store.engineered_data.set(None)
            status_store.set("Working copy synced from cleaned data.")

    @reactive.effect
    @reactive.event(input.reset_features)
    def _reset_features():
        df = shared_store.cleaned_data()
        if df is not None:
            working_copy.set(df.copy())
            feature_history_store.set([])
            undo_history.set([])
            shared_store.engineered_data.set(df.copy())
            status_store.set("Reset complete. Working data restored to cleaned data.")

    @render.ui
    def column_selector_ui():
        df = working_copy()
        if df is None:
            return ui.p("No data available", class_="text-muted")

        numeric_cols = df.select_dtypes(include="number").columns.tolist()

        if input.operation_type() == "single":
            if not numeric_cols:
                return ui.p("No numeric columns found.", class_="text-warning")
            return ui.input_select(
                "target_column",
                "Select Numeric Column",
                choices=numeric_cols,
            )

        if input.operation_type() == "datetime":
            dt_cols = _datetime_candidate_columns(df)
            if not dt_cols:
                return ui.p(
                    "No datetime columns found, and no text column parsed as dates. "
                    "Load data with a datetime column or date strings.",
                    class_="text-warning",
                )
            return ui.input_select(
                "datetime_column",
                "Date / Time Column",
                choices=dt_cols,
            )

        if len(numeric_cols) < 2:
            return ui.p("At least two numeric columns are required for combination features.", class_="text-warning")

        return ui.TagList(
            ui.input_select("first_column", "First Numeric Column", choices=numeric_cols),
            ui.input_select("second_column", "Second Numeric Column", choices=numeric_cols),
        )

    @render.ui
    def operation_controls_ui():
        if input.operation_type() == "single":
            return ui.TagList(
                ui.input_select(
                    "transform_type",
                    "Transformation",
                    choices={
                        "log": "Log Transform (ln)",
                        "log1p": "Log1p Transform (ln(1+x))",
                        "sqrt": "Square Root",
                        "square": "Square",
                        "zscore": "Standardization (Z-score)",
                        "minmax": "Min-Max Scaling",
                        "binning": "Binning",
                    },
                ),
                ui.output_ui("binning_ui"),
            )

        if input.operation_type() == "datetime":
            return ui.input_select(
                "datetime_part",
                "Extract",
                choices={
                    "year": "Calendar year",
                    "month": "Month (1–12)",
                    "day": "Day of month",
                    "dayofweek": "Day of week (0=Mon … 6=Sun)",
                    "hour": "Hour (0–23)",
                    "minute": "Minute (0–59)",
                    "quarter": "Quarter (1–4)",
                    "is_weekend": "Is weekend (1=yes, 0=no)",
                    "dayofyear": "Day of year (1–366)",
                },
            )

        return ui.input_select(
            "combine_type",
            "Combination Method",
            choices={
                "add": "Add (x1 + x2)",
                "multiply": "Multiply (x1 × x2)",
                "ratio": "Ratio (x1 / x2)",
            },
        )

    @render.ui
    def binning_ui():
        if input.operation_type() == "single" and input.transform_type() == "binning":
            return ui.input_slider(
                "num_bins",
                "Number of Bins",
                min=2,
                max=10,
                value=4,
            )
        return ui.TagList()

    @render.ui
    def transform_help():
        """Per-operation / per-transform English explanations for the rubric."""
        if working_copy() is None:
            return ui.TagList()

        op = input.operation_type()
        title = ui.tags.strong("What this transformation does")

        if op == "single":
            tt = input.transform_type()
            body = _SINGLE_TRANSFORM_HELP.get(tt, "")
            return ui.div(
                title,
                ui.p(body, class_="small text-muted mb-0 mt-1"),
                class_="border rounded p-2 mb-2 bg-light",
            )

        if op == "combine":
            ct = input.combine_type()
            body = _COMBINE_HELP.get(ct, "")
            return ui.div(
                title,
                ui.p(body, class_="small text-muted mb-0 mt-1"),
                class_="border rounded p-2 mb-2 bg-light",
            )

        if op == "datetime":
            part = input.datetime_part()
            body = _DATETIME_PART_HELP.get(
                part,
                "Extracts a date/time component from the selected column for seasonality or calendar effects.",
            )
            return ui.div(
                title,
                ui.p(body, class_="small text-muted mb-0 mt-1"),
                class_="border rounded p-2 mb-2 bg-light",
            )

        return ui.TagList()

    def _datetime_candidate_columns(df: pd.DataFrame) -> list[str]:
        """Columns that are datetimes or object/strings that may parse as dates."""
        out: list[str] = []
        for c in df.columns:
            s = df[c]
            if pd.api.types.is_datetime64_any_dtype(s):
                out.append(c)
            elif s.dtype == object or pd.api.types.is_string_dtype(s):
                sample = s.dropna().head(50)
                if len(sample) == 0:
                    continue
                parsed = pd.to_datetime(sample, errors="coerce")
                if parsed.notna().sum() >= max(1, len(sample) // 2):
                    out.append(c)
        return out

    def _series_as_datetime(series: pd.Series) -> pd.Series:
        if pd.api.types.is_datetime64_any_dtype(series):
            return series
        return pd.to_datetime(series, errors="coerce")

    def _safe_feature_name(default_name: str) -> str:
        custom_name = input.custom_feature_name().strip()
        return custom_name if custom_name else default_name

    @reactive.calc
    def live_preview():
        """Compute transform preview reactively based on current sidebar selections."""
        df = working_copy()
        if df is None:
            return None, {}

        result = df.copy()
        try:
            if input.operation_type() == "single":
                col = input.target_column()
                transform = input.transform_type()
                if col not in result.columns:
                    return None, {}

                if transform == "log":
                    new_col_name = _safe_feature_name(f"{col}_log")
                    result[new_col_name] = np.log(result[col].clip(lower=1e-10))
                elif transform == "log1p":
                    new_col_name = _safe_feature_name(f"{col}_log1p")
                    result[new_col_name] = np.log1p(result[col].clip(lower=0))
                elif transform == "sqrt":
                    new_col_name = _safe_feature_name(f"{col}_sqrt")
                    result[new_col_name] = np.sqrt(result[col].clip(lower=0))
                elif transform == "square":
                    new_col_name = _safe_feature_name(f"{col}_square")
                    result[new_col_name] = np.square(result[col])
                elif transform == "zscore":
                    new_col_name = _safe_feature_name(f"{col}_zscore")
                    std = result[col].std()
                    if std == 0 or pd.isna(std):
                        return None, {}
                    result[new_col_name] = (result[col] - result[col].mean()) / std
                elif transform == "minmax":
                    new_col_name = _safe_feature_name(f"{col}_minmax")
                    col_min, col_max = result[col].min(), result[col].max()
                    if col_min == col_max:
                        return None, {}
                    result[new_col_name] = (result[col] - col_min) / (col_max - col_min)
                elif transform == "binning":
                    bins = input.num_bins()
                    new_col_name = _safe_feature_name(f"{col}_binned")
                    result[new_col_name] = pd.cut(result[col], bins=bins, include_lowest=True).astype(str)
                else:
                    return None, {}

                return result, {"mode": "single", "source_col": col, "new_col": new_col_name}

            elif input.operation_type() == "datetime":
                col = input.datetime_column()
                part = input.datetime_part()
                if col not in result.columns:
                    return None, {}

                ts = _series_as_datetime(result[col])
                if ts.notna().sum() == 0:
                    return None, {}

                suffix = {"year": "year", "month": "month", "day": "day", "dayofweek": "dow",
                           "hour": "hour", "minute": "minute", "quarter": "quarter",
                           "is_weekend": "weekend", "dayofyear": "doy"}.get(part, part)
                new_col_name = _safe_feature_name(f"{col}_{suffix}")

                part_map = {
                    "year": ts.dt.year, "month": ts.dt.month, "day": ts.dt.day,
                    "dayofweek": ts.dt.dayofweek, "hour": ts.dt.hour, "minute": ts.dt.minute,
                    "quarter": ts.dt.quarter, "is_weekend": ts.dt.dayofweek.isin([5, 6]).astype(int),
                    "dayofyear": ts.dt.dayofyear,
                }
                if part not in part_map:
                    return None, {}
                result[new_col_name] = part_map[part]
                return result, {"mode": "datetime", "source_col": col, "new_col": new_col_name}

            else:  # combine
                col1 = input.first_column()
                col2 = input.second_column()
                combine_type = input.combine_type()
                if col1 not in result.columns or col2 not in result.columns:
                    return None, {}

                if combine_type == "add":
                    new_col_name = _safe_feature_name(f"{col1}_plus_{col2}")
                    result[new_col_name] = result[col1] + result[col2]
                elif combine_type == "multiply":
                    new_col_name = _safe_feature_name(f"{col1}_times_{col2}")
                    result[new_col_name] = result[col1] * result[col2]
                elif combine_type == "ratio":
                    new_col_name = _safe_feature_name(f"{col1}_div_{col2}")
                    denominator = result[col2].replace(0, np.nan)
                    result[new_col_name] = result[col1] / denominator
                else:
                    return None, {}

                return result, {"mode": "combine", "source_col": col1, "second_col": col2, "new_col": new_col_name}

        except Exception:
            return None, {}

    @reactive.effect
    @reactive.event(input.apply_transform)
    def _apply():
        df, meta = live_preview()

        if df is None or not meta:
            status_store.set("Nothing to apply. Please select a column and transformation.")
            return

        current = working_copy()
        if current is not None:
            _push_history(current)

        working_copy.set(df.copy())

        history = feature_history_store().copy()
        new_feature = meta.get("new_col")
        if new_feature and new_feature not in history:
            history.append(new_feature)
            feature_history_store.set(history)

        status_store.set(f"Applied: {new_feature}. Click Save to push to pipeline.")

    @reactive.effect
    @reactive.event(input.save_to_pipeline)
    def _save():
        df = working_copy()
        if df is None:
            status_store.set("No data to save.")
            return
        shared_store.engineered_data.set(df.copy())
        status_store.set(f"Saved to pipeline: {df.shape[0]} rows, {df.shape[1]} columns.")
        ui.notification_show("Engineered data saved to pipeline.", type="message")

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

        # Remove last feature from history
        history = feature_history_store().copy()
        if history:
            history.pop()
            feature_history_store.set(history)

        msg = f"Undo successful. ({len(stack)} step(s) remaining)"
        if shared_store.engineered_data() is not None:
            msg += " ⚠ Saved pipeline data is now out of sync. Click Save to update."
        ui.notification_show(msg, type="warning" if shared_store.engineered_data() is not None else "message")

    @render.ui
    def status_message():
        msg = status_store()
        if not msg:
            return ui.TagList()
        return ui.div(msg, class_="alert alert-info")

    @render.data_frame
    def transform_preview():
        df, meta = live_preview()
        if df is None:
            return pd.DataFrame()
        if meta and meta.get("new_col") in df.columns:
            cols_to_show = [meta.get("source_col"), meta.get("new_col")]
            if meta.get("mode") == "combine":
                cols_to_show = [meta.get("source_col"), meta.get("second_col"), meta.get("new_col")]
            cols_to_show = list(dict.fromkeys(c for c in cols_to_show if c in df.columns))
            return render.DataGrid(df[cols_to_show], height="100%")
        return pd.DataFrame()

    @render.data_frame
    def current_data():
        df = working_copy()
        if df is None:
            return pd.DataFrame()
        return render.DataGrid(df, height="100%")

    @render_widget
    def before_plot():
        df = working_copy()
        if df is None:
            return go.Figure(layout=go.Layout(title="Select a column to see its distribution."))

        _, meta = live_preview()

        if not meta:
            return go.Figure(layout=go.Layout(title="Select a column to see its distribution."))

        source_col = meta.get("source_col")
        if source_col not in df.columns:
            return go.Figure(layout=go.Layout(title="Source column not found."))

        if meta.get("mode") == "datetime":
            ts = _series_as_datetime(df[source_col])
            tdf = pd.DataFrame({"time": ts.dropna()})
            if tdf.empty:
                return go.Figure(layout=go.Layout(title="No parseable dates for plotting."))
            fig = px.histogram(tdf, x="time", nbins=30, title=f"Before: {source_col} (parsed timeline)")
            fig.update_layout(template="plotly_white")
            return fig

        if not pd.api.types.is_numeric_dtype(df[source_col]):
            return go.Figure(layout=go.Layout(title="No numeric source column available for plotting."))

        fig = px.histogram(df, x=source_col, nbins=20, title=f"Before: {source_col}")
        fig.update_layout(template="plotly_white")
        return fig

    @render_widget
    def after_plot():
        df, meta = live_preview()

        if df is None or not meta:
            return go.Figure(layout=go.Layout(title="Select a transformation to see the result."))

        new_col = meta.get("new_col")
        if new_col not in df.columns:
            return go.Figure(layout=go.Layout(title="Preview feature not found."))

        if pd.api.types.is_numeric_dtype(df[new_col]):
            fig = px.histogram(
                df,
                x=new_col,
                nbins=20,
                title=f"After: {new_col}",
            )
        else:
            counts = df[new_col].value_counts(dropna=False).reset_index()
            counts.columns = [new_col, "count"]
            fig = px.bar(
                counts,
                x=new_col,
                y="count",
                title=f"After: {new_col}",
            )

        fig.update_layout(template="plotly_white")
        return fig

    @render.ui
    def feature_history():
        history = feature_history_store()
        if not history:
            return ui.p("No engineered features have been saved yet.", class_="text-muted")
        return ui.tags.ul([ui.tags.li(name) for name in history])

    @reactive.effect
    @reactive.event(input.go_to_eda)
    def _go_to_eda():
        target = app_session if app_session is not None else session
        ui.update_navs("main_nav", selected="EDA", session=target)
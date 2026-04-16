"""
Exploratory Data Analysis (EDA) Module — Member 4

Reads: shared_store.raw_data, shared_store.cleaned_data, shared_store.engineered_data
Writes: nothing (read-only analysis)
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
from shiny import Inputs, Outputs, Session, module, reactive, render, ui
from shinywidgets import output_widget, render_widget

@module.ui
def eda_ui():
    return ui.layout_sidebar(
        ui.sidebar(
            ui.h4("EDA Controls"),
            ui.input_select(
                "data_stage",
                "Select Data Stage",
                choices={"raw": "Raw Data", "cleaned": "Cleaned Data", "engineered": "Engineered Data"},
            ),
            ui.hr(),

            # =================================================================
            # === 1. STATIC FILTERING UI (STABLE) ===
            # =================================================================
            ui.h5("1. Filter Data"),

            # Numeric Variable Filter
            ui.input_select("filter_num_col", "Numeric Filter:", choices=["None"]),
            ui.panel_conditional(
                "input.filter_num_col !== 'None'",
                ui.input_slider("filter_num_val", "Select Range", min=0, max=100, value=[0, 100])
            ),

            # Category-type variable filter
            ui.input_select("filter_cat_col", "Categorical Filter:", choices=["None"]),
            ui.panel_conditional(
                "input.filter_cat_col !== 'None'",
                ui.input_select("filter_cat_val", "Select Categories", choices=[], multiple=True)
            ),

            ui.hr(),

            # =================================================================
            # === 2. PLOT SETTINGS UI ===
            # =================================================================
            ui.h5("2. Plot Settings"),
            ui.input_select("plot_type", "Select Plot Type", choices=[
                "Scatter Plot", "Bar Chart (Average)", "Box Plot",
                "Histogram", "Violin Plot", "Pie Chart",
            ]),
            ui.input_select("x_var", "X Variable", choices=["Waiting for data..."]),
            ui.panel_conditional(
                "input.plot_type !== 'Histogram' && input.plot_type !== 'Pie Chart'",
                ui.input_select("y_var", "Y Variable", choices=["Waiting for data..."]),
            ),
            ui.panel_conditional(
                "input.plot_type !== 'Pie Chart'",
                ui.input_select("color_var", "Color / Group By (Optional)", choices=["None"]),
            ),
            ui.panel_conditional(
                "input.plot_type === 'Scatter Plot'",
                ui.input_checkbox("add_trendline", "Add Trendline", value=False),
            ),
            ui.panel_conditional(
                "input.plot_type === 'Histogram'",
                ui.input_slider("hist_bins", "Number of Bins", min=5, max=100, value=20),
            ),

            ui.hr(),
            ui.p("💡 Tip: Download plots using the camera icon in the top right corner.", class_="text-muted", style="font-size: 0.85em;"),

            width=320,
        ),

        # Main panel
        ui.output_ui("guard_message"),
        ui.navset_card_tab(
            ui.nav_panel("Interactive Plot", output_widget("interactive_plot")),
            ui.nav_panel(
                "Pair Plot",
                ui.input_selectize("pair_plot_cols", "Select columns:", choices=[], multiple=True, width="100%"),
                output_widget("pair_plot"),
            ),
            ui.nav_panel(
                "Correlation Heatmap",
                ui.div(
                    ui.input_numeric("heatmap_max_cols", "Max columns:", value=30, min=2, max=100, width="150px"),
                    style="display: flex; justify-content: flex-end; margin-bottom: 4px;",
                ),
                output_widget("heatmap_plot"),
            ),
            ui.nav_panel("Summary Statistics", ui.output_data_frame("summary_table")),
        ),
    )


@module.server
def eda_server(input: Inputs, output: Outputs, session: Session, shared_store, app_session=None,group_label=None,):

    @render.ui
    def guard_message():
        if shared_store.raw_data() is None:
            return ui.div(
                ui.h4("No data available"),
                ui.p("Please go to the Data Loading tab and upload or select a dataset first."),
                class_="alert alert-warning",
            )
        return ui.TagList()
    
    def emit_ga(event_name: str, extra_params: dict | None = None):
        target_session = app_session if app_session is not None else session
        params = {
            "group": group_label,
            "tab_name": "EDA",
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
    # =========================================================================
    # === BASE DATA ===
    # =========================================================================
    @reactive.calc
    def base_data() -> pd.DataFrame | None:
        stage = input.data_stage()
        if stage == "raw": return shared_store.raw_data()
        elif stage == "cleaned": return shared_store.cleaned_data()
        elif stage == "engineered": return shared_store.engineered_data()
        return None

    # =========================================================================
    # === SERVER-SIDE UI UPDATES (The most stable approach) ===
    # =========================================================================
    @reactive.effect
    def update_all_dropdowns():
        """When the data is loaded, assign all column names to their corresponding drop-down menus"""
        df = base_data()
        if df is None or df.empty: return

        all_cols = df.columns.tolist()
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()

        ui.update_select("filter_num_col", choices=["None"] + num_cols)
        ui.update_select("filter_cat_col", choices=["None"] + cat_cols)

        ui.update_select("color_var", choices=["None"] + all_cols)
        ui.update_selectize("pair_plot_cols", choices=num_cols, selected=num_cols[:4])

    @reactive.effect
    def update_plot_type_choices():
        """Update x/y variable choices based on the selected plot type."""
        df = base_data()
        if df is None or df.empty:
            return

        all_cols = df.columns.tolist()
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        plot_type = input.plot_type()

        if plot_type in ["Violin Plot", "Pie Chart"]:
            x_choices = cat_cols if cat_cols else all_cols
        else:
            x_choices = all_cols

        ui.update_select("x_var", choices=x_choices)

        if plot_type in ["Scatter Plot", "Bar Chart (Average)", "Box Plot", "Violin Plot"]:
            ui.update_select("y_var", choices=num_cols if num_cols else all_cols)

    @reactive.effect
    def update_slider_range():
        """When the user selects a column for numerical filtering, update the maximum and minimum values of the slider"""
        df = base_data()
        col = input.filter_num_col()
        if df is not None and col != "None" and col in df.columns:
            cmin, cmax = float(df[col].min()), float(df[col].max())
            if cmin == cmax: cmax += 0.01 # 防止数据全一样导致报错
            ui.update_slider("filter_num_val", min=cmin, max=cmax, value=[cmin, cmax])

    @reactive.effect
    def update_category_choices():
        """When the user selects the category filter column, update the options in the checkbox"""
        df = base_data()
        col = input.filter_cat_col()
        if df is not None and col != "None" and col in df.columns:
            vals = df[col].dropna().unique().tolist()
            ui.update_select("filter_cat_val", choices=vals, selected=vals)

    # =========================================================================
    # === FILTER ENGINE ===
    # =========================================================================
    @reactive.calc
    def filtered_data() -> pd.DataFrame | None:
        df = base_data()
        if df is None or df.empty: return None

        # 1. Apply a numerical filter
        num_col = input.filter_num_col()
        if num_col != "None" and num_col in df.columns:
            f_range = input.filter_num_val()
            cmin, cmax = df[num_col].min(), df[num_col].max()
            # Fault-tolerance mechanism: Prevents data from being accidentally cleared due to delays in UI updates
            if not (f_range[1] < cmin or f_range[0] > cmax):
                df = df[(df[num_col] >= f_range[0]) & (df[num_col] <= f_range[1])]

        # 2. Apply category filter
        cat_col = input.filter_cat_col()
        if cat_col != "None" and cat_col in df.columns:
            f_vals = input.filter_cat_val()
            if f_vals is not None:
                if len(f_vals) > 0:
                    df = df[df[cat_col].isin(list(f_vals))]
                else:
                    df = df.iloc[0:0] # If none are selected, return an empty dataset

        return df

    # =========================================================================
    # === RENDER PLOTS & TABLES ===
    # =========================================================================
    @render_widget
    def interactive_plot():
        df = filtered_data()
        if df is None or df.empty:
            return px.scatter(title="No data available or all data filtered out.")

        x_col = input.x_var()
        plot_type = input.plot_type()

        if x_col == "Waiting for data..." or x_col not in df.columns:
            return px.scatter(title="Please select valid X variable.")

        # Plots that only need X
        if plot_type == "Histogram":
            color_col = input.color_var()
            c_val = None if color_col == "None" or color_col not in df.columns else color_col
            if pd.api.types.is_numeric_dtype(df[x_col]):
                fig = px.histogram(
                    df, x=x_col, color=c_val,
                    nbins=input.hist_bins(),
                    title=f"Histogram: {x_col}",
                )
            else:
                counts = df[x_col].value_counts(dropna=False).reset_index()
                counts.columns = [x_col, "count"]
                fig = px.bar(counts, x=x_col, y="count", title=f"Value Counts: {x_col}")
   
            fig.update_layout(template="plotly_white")



            return fig
        
        if plot_type == "Pie Chart":
            counts = df[x_col].value_counts(dropna=False)
            if len(counts) > 20:
                top = counts.head(19)
                top["Other"] = counts.iloc[19:].sum()
                counts = top
            pie_df = counts.reset_index()
            pie_df.columns = [x_col, "count"]
            fig = px.pie(pie_df, names=x_col, values="count", title=f"Pie Chart: {x_col}")
            fig.update_layout(template="plotly_white")


            return fig

        # Plots that need X + Y
        y_col = input.y_var()
        if y_col not in df.columns:
            return px.scatter(title="Please select a valid Y variable.")

        color_col = input.color_var()
        c_val = None if color_col == "None" or color_col not in df.columns else color_col

        if plot_type in ["Bar Chart (Average)", "Box Plot", "Violin Plot"] and not pd.api.types.is_numeric_dtype(df[y_col]):
            return px.scatter(title=f"Error: Y Variable '{y_col}' must be numeric for {plot_type}.")

        if plot_type == "Scatter Plot":
            trend = "ols" if input.add_trendline() else None
            fig = px.scatter(
                df, x=x_col, y=y_col, color=c_val,
                trendline=trend,
                title=f"Scatter Plot: {y_col} vs {x_col}",
                opacity=0.7
            )
        elif plot_type == "Bar Chart (Average)":
            fig = px.histogram(
                df, x=x_col, y=y_col, color=c_val,
                histfunc='avg', barmode='group',
                title=f"Bar Chart: Average {y_col} by {x_col}"
            )
            fig.update_layout(yaxis_title=f"Average of {y_col}")
        elif plot_type == "Box Plot":
            fig = px.box(
                df, x=x_col, y=y_col, color=c_val,
                title=f"Box Plot: Distribution of {y_col} across {x_col}"
            )
        elif plot_type == "Violin Plot":
            fig = px.violin(
                df, x=x_col, y=y_col, color=c_val,
                box=True, points="outliers",
                title=f"Violin Plot: {y_col} by {x_col}"
            )
        else:
            return px.scatter(title=f"Unknown plot type: {plot_type}")

        fig.update_layout(template="plotly_white")

        return fig

    @render_widget
    def pair_plot():
        df = filtered_data()
        if df is None or df.empty:
            return px.scatter(title="No data available.")

        selected = list(input.pair_plot_cols())
        cols = [c for c in selected if c in df.columns]

        if len(cols) < 2:
            return px.scatter(title="Select at least 2 numeric columns.")

        n = len(cols)
        size = max(600, n * 150)

        fig = px.scatter_matrix(
            df, dimensions=cols,
            title=f"Pair Plot ({n} columns)",
            opacity=0.5,
        )
        fig.update_traces(diagonal_visible=True, showupperhalf=False)
        fig.update_layout(template="plotly_white", height=max(700, n * 200), autosize=True)

        return fig

    @render_widget
    def heatmap_plot():
        df = filtered_data()
        if df is None or df.empty:
            return px.imshow([[0]], title="No data available.")

        numeric_df = df.select_dtypes(include="number")
        if numeric_df.empty or numeric_df.shape[1] < 2:
            return px.imshow([[0]], title="Not enough numeric columns for heatmap")

        MAX_COLS = input.heatmap_max_cols() or 30
        if numeric_df.shape[1] > MAX_COLS:
            total = numeric_df.shape[1]
            numeric_df = numeric_df.iloc[:, :MAX_COLS]
            title = f"Correlation Matrix (first {MAX_COLS} of {total} numeric columns)"
        else:
            title = "Correlation Matrix of Numeric Variables (Filtered)"

        corr_matrix = numeric_df.corr().round(2)
        fig = px.imshow(
            corr_matrix,
            text_auto=numeric_df.shape[1] <= 20,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title=title,
        )
        fig.update_layout(template="plotly_white")

        return fig

    @render.data_frame
    def summary_table():
        df = filtered_data()
        if df is None or df.empty:
            return pd.DataFrame()
        desc = df.describe(include="all").T
        desc.insert(0, "column", desc.index)
        desc = desc.reset_index(drop=True)
        return render.DataGrid(desc, filters=False)

"""
STAT5243 Project 2 — Data Preprocessing & EDA Web Application

Main entry point. Wires together all modules, the shared data store,
and the navbar layout. Run with:  shiny run app.py
"""

import os

from shiny import App, Inputs, Outputs, Session, ui

import shinyswatch

from shared.data_store import SharedDataStore
from modules.user_guide_c import user_guide_ui
from modules.data_loading_c import data_loading_ui, data_loading_server
from modules.data_cleaning import data_cleaning_ui, data_cleaning_server
from modules.feature_engineering import feature_engineering_ui, feature_engineering_server
from modules.eda import eda_ui, eda_server

# Set to True to pre-fill all pipeline stages with sample data.
# Useful for independent module development / testing.
DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"

_GLOBAL_CSS = ui.tags.style(
    "html, body { height: 100%; }"
    ".bslib-page-fill { min-height: 100vh; }"
    ".tab-content, .tab-pane.active {"
    "  display: flex; flex-direction: column; flex: 1 1 auto; min-height: 0;"
    "}"
    ".bslib-sidebar-layout {"
    "  grid-template-columns: auto 1fr !important;"
    "  flex: 1 1 auto;"
    "  min-height: 0;"
    "  grid-template-rows: 1fr !important;"
    "}"
    ".bslib-sidebar-layout > .sidebar {"
    "  resize: horizontal;"
    "  overflow: auto;"
    "  min-width: 180px;"
    "  max-width: 50vw;"
    "  width: 320px;"
    "  align-self: stretch;"
    "}"
    ".bslib-sidebar-layout > .main {"
    "  display: flex;"
    "  flex-direction: column;"
    "  min-height: 0;"
    "}"
    ".bslib-sidebar-layout > .main > .card {"
    "  flex: 1 1 auto;"
    "  min-height: 0;"
    "}"
    "#shiny-notification-panel {"
    "  top: 0;"
    "  bottom: unset !important;"
    "}"
)

app_ui = ui.page_navbar(
    ui.nav_panel("User Guide", user_guide_ui("user_guide")),
    ui.nav_panel("Data Loading", data_loading_ui("data_loading")),
    ui.nav_panel("Data Cleaning", data_cleaning_ui("data_cleaning")),
    ui.nav_panel("Feature Engineering", feature_engineering_ui("feature_engineering")),
    ui.nav_panel("EDA", eda_ui("eda")),
    ui.head_content(_GLOBAL_CSS),
    title="Data Explorer",
    id="main_nav",
    theme=shinyswatch.theme.flatly,
    fillable=True,
)


def server(input: Inputs, output: Outputs, session: Session):
    store = SharedDataStore()

    if DEV_MODE:
        store.dev_mode_init()

    data_loading_server("data_loading", shared_store=store, app_session=session)
    data_cleaning_server("data_cleaning", shared_store=store, app_session=session)
    feature_engineering_server("feature_engineering", shared_store=store, app_session=session)
    eda_server("eda", shared_store=store)


app = App(app_ui, server)

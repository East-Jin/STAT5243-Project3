"""
STAT5243 Project 3 

Main entry point. Wires together all modules, the shared data store,
and the navbar layout. Run with:  shiny run app_B.py
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

GOOGLE_TAG = ui.head_content(
    ui.tags.script(
        async_="",
        src="https://www.googletagmanager.com/gtag/js?id=G-4VCD59ZG2X"
    ),
    ui.tags.script(
        """
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'G-4VCD59ZG2X',{'debug_mode':true});

        // Identify this as CONTROL group
        gtag('event', 'ab_group', {
            group: 'B'
        });

        (function () {
            let currentTab = null;
            let tabStartTime = null;

            function gaEvent(name, params) {
                if (typeof gtag !== "function") return;
                gtag('event', name, params || {});
            }

            function getActiveTabName() {
                const active = document.querySelector('.nav-link.active');
                return active ? active.textContent.trim() : null;
            }

            function startTabTiming(tabName) {
                if (!tabName) return;
                currentTab = tabName;
                tabStartTime = Date.now();

                gaEvent('tab_view', {
                    tab_name: tabName,
                    group: 'B'
                });
            }

            function stopTabTiming() {
                if (!currentTab || !tabStartTime) return;

                const durationMs = Date.now() - tabStartTime;

                gaEvent('tab_engagement', {
                    tab_name: currentTab,
                    group: 'B',
                    value: durationMs,
                    engagement_seconds: Math.round(durationMs / 1000)
                });

                currentTab = null;
                tabStartTime = null;
            }

            document.addEventListener('DOMContentLoaded', function () {
                startTabTiming(getActiveTabName());
            });

            document.addEventListener('click', function (e) {
                const nav = e.target.closest('.nav-link');
                if (nav) {
                    const nextTab = nav.textContent.trim();
                    if (nextTab && nextTab !== currentTab) {
                        stopTabTiming();
                        setTimeout(function () {
                            startTabTiming(nextTab);
                        }, 0);
                    }
                    return;
                }

                const button = e.target.closest('button');
                if (button) {
                    const buttonId = button.id || '';
                    const buttonName = (button.textContent || '').trim();

                    gaEvent('button_click', {
                        group: 'B',
                        tab_name: getActiveTabName(),
                        button_id: buttonId,
                        button_name: buttonName
                    });

                    // Optional: map important buttons to cleaner event names
                    const idLower = buttonId.toLowerCase();
                    const nameLower = buttonName.toLowerCase();

                    if (idLower.includes('load') || nameLower.includes('load dataset')) {
                        gaEvent('load_dataset_click', {
                            group: 'B',
                            tab_name: getActiveTabName()
                        });
                    }

                    if (nameLower.includes('apply and save')) {
                        gaEvent('cleaning_apply_and_save_click', {
                            group: 'B',
                            tab_name: getActiveTabName()
                        });
                    }

                    if (nameLower === 'apply') {
                        gaEvent('feature_apply_click', {
                            group: 'B',
                            tab_name: getActiveTabName()
                        });
                    }

                    if (nameLower.includes('save to pipeline')) {
                        gaEvent('feature_save_to_pipeline_click', {
                            group: 'B',
                            tab_name: getActiveTabName()
                        });
                    }
                }

                const titled = e.target.closest('[title],[data-title]');
                if (titled) {
                    const title = (
                        titled.getAttribute('title') ||
                        titled.getAttribute('data-title') ||
                        ''
                    ).trim();

                    if (title === 'Download plot as a PNG') {
                        gaEvent('plot_download_png_click', {
                            group: 'B',
                            tab_name: getActiveTabName()
                        });
                    }
                }
            });

            document.addEventListener('visibilitychange', function () {
                if (document.hidden) {
                    stopTabTiming();
                } else {
                    startTabTiming(getActiveTabName());
                }
            });

            window.addEventListener('beforeunload', function () {
                stopTabTiming();
            });
        })();
         // Watch for dataset_loaded_success
            (function() {
                let datasetLoaded = false;
                const loadObserver = new MutationObserver(function() {
                    const badge = document.querySelector('.badge.bg-success');
                    if (badge && !datasetLoaded) {
                        datasetLoaded = true;
                        gaEvent('dataset_loaded_success', {
                            group: 'B', 
                            tab_name: 'Data Loading',
                            dataset_name: badge.textContent.replace('Dataset: ', '').trim()
                        });
                    }
                });
                loadObserver.observe(document.body, { childList: true, subtree: true });

                // Reset when new dataset loaded
                document.addEventListener('click', function(e) {
                    const btn = e.target.closest('button');
                    if (btn && (btn.id || '').toLowerCase().includes('confirm_load') || 
                        (btn.textContent || '').toLowerCase().includes('load dataset')) {
                        datasetLoaded = false;
                    }
                });
            })();

            document.addEventListener("shiny:connected", function () {

            Shiny.addCustomMessageHandler('ga_event', function(message) {

                if (typeof gtag !== "function") return;

                const eventName = message.event_name;
                const params = message.params || {};

                gtag('event', eventName, params);

            });

});

        """
    )
)

app_ui = ui.page_navbar(
    ui.nav_panel("User Guide", user_guide_ui("user_guide")),
    ui.nav_panel("Data Loading", data_loading_ui("data_loading")),
    ui.nav_panel("Data Cleaning", data_cleaning_ui("data_cleaning")),
    ui.nav_panel("Feature Engineering", feature_engineering_ui("feature_engineering")),
    ui.nav_panel("EDA", eda_ui("eda")),
    GOOGLE_TAG,
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

    data_loading_server("data_loading", shared_store=store, app_session=session,group_label="B")
    data_cleaning_server("data_cleaning", shared_store=store, app_session=session,group_label="B")
    feature_engineering_server("feature_engineering", shared_store=store, app_session=session,group_label="B")
    eda_server("eda", shared_store=store,app_session=session,group_label="B")


app = App(app_ui, server)

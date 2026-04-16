from shiny import App, ui

CONTROL_URL = "https://dz2590.shinyapps.io/project3-1"
TREATMENT_URL = "https://dz2590.shinyapps.io/project3-2"

GA_TAG = ui.head_content(
    ui.tags.script(
        src="https://www.googletagmanager.com/gtag/js?id=G-4VCD59ZG2X",
        async_=""
    ),
    ui.tags.script("""
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'G-4VCD59ZG2X');
    """)
)

app_ui = ui.page_fluid(
    GA_TAG,

    ui.tags.script(f"""
        (function() {{

            let group = localStorage.getItem("ab_group_project3");

            if (!group) {{
                group = Math.random() < 0.5 ? "A" : "B";
                localStorage.setItem("ab_group_project3", group);
            }}

            // log experiment assignment
            gtag('event', 'experiment_assignment', {{
                variant: group,
                experiment_name: 'project3_ab_test'
            }});

            // 300 ms delay before redirect
            setTimeout(function() {{

                if (group === "A") {{
                    window.location.replace("{CONTROL_URL}?group=A");
                }} else {{
                    window.location.replace("{TREATMENT_URL}?group=B");
                }}

            }}, 300);

        }})();
    """)
)

def server(input, output, session):
    pass

app = App(app_ui, server)
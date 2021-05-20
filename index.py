from dash_bootstrap_components._components.NavLink import NavLink
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from server import app, config
from apps import home, classification, add_class, remove_class, error


PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

navbar = dbc.NavbarSimple(
    [   
        dbc.NavItem(dbc.NavLink("Home", href="/home")),
        dbc.DropdownMenu(
            children=[
                # dbc.DropdownMenuItem("More pages", header=True),
                dbc.DropdownMenuItem("Classification", href="classification"),
                dbc.DropdownMenuItem("Add Class", href="add-class"),
                dbc.DropdownMenuItem("Remove Class", href="remove-class"),
            ],
            nav=True,
            in_navbar=True,
            label="Navigate",
        ),
    ],
    color="dark",
    dark=True,
    brand="MITB Incremental Learner",
    className="d-none",
    id="app-navbar"
)

app.layout = dbc.Container(
    [
        navbar,
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content', className="page-content")
    ],
    fluid=True,
    id="main-container",
    className="p-0"
)


@app.callback([Output('app-navbar', 'className'),
               Output('page-content', 'children'),
               Output('page-content', 'className')],
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/' or pathname == '/home':
        return ("d-none", home.layout, 'page-content')
    elif pathname == '/classification':
        return ("fixed-top", classification.layout, 'page-content mt-5')
    elif pathname == '/add-class':
        return ("fixed-top", add_class.layout, 'page-content mt-5')
    elif pathname == '/remove-class':
        # Remove class is special as it is dependent on the shell_classifier's state on first render
        # Hence, need to call a function to re-generate it whenever it is navigated to that page.
        return ("fixed-top", remove_class.load_layout(), 'page-content mt-5')
    else:
        return ("fixed-top", error.layout, 'page-content mt-5')

if __name__ == '__main__':
    app.run_server(host=config['environment']['host'],
                   port=config['environment']['port'],
                   debug=config['environment']['debug'])
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from server import app

error_jumbotron = dbc.Jumbotron(
    [
        html.H1("404: Page Not Found!", className="display-3"),
        html.Hr(className="my-2"),
        html.P(
            "Please use the navigation bar above to navigate to the correct pages!",
            className="lead",
        ),
    ]
)

layout = dbc.Container(
    [
        error_jumbotron
    ],
    fluid=False
)
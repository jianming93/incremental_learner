import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from server import app

title_jumbotron = dbc.Jumbotron(
    [
        dbc.Container(
            [
                html.H1("MITB Incremental Learning", className="display-2 d-flex justify-content-center"),
                html.P(
                    "Project by Prof Daniel Lin and Ng Jian Ming",
                    className="lead d-flex justify-content-center",
                    id="home-page-content"
                ),
                # html.Hr(),
                # html.H1("About", className="display-5 d-flex justify-content-start"),
            ],
            fluid=True,
        )
    ],
    fluid=True,
    className="mb-0 home-jumbotron d-flex align-items-center"
)

info_jumbotron = dbc.Jumbotron(
    [
        dbc.Container(
            [
                html.H1("About", className="display-5 d-flex"),
                html.P(
                    "The incremental learner aims to explore how to quickly adopt to different "
                    "classes",
                    className="lead d-flex",
                    id="home-page-content"
                ),
            ],
            fluid=True,
        )
    ],
    fluid=False,
    className="mb-0 info-jumbotron d-flex"
)

classification_card = dbc.Card(
    [
        dbc.CardImg(src="assets/classification-logo.png", top=True, className="card-img d-flex justify-content-center mx-auto"),
        dbc.CardBody(
            [
                html.H4("Classification", className="card-title d-flex justify-content-center"),
                html.P(
                    "Demo of classification for incremental learner system.",
                    className="card-text d-flex justify-content-center",
                ),
                dbc.Button("Classification Page", color="primary", className="card-nav-button", href='/classification'),
            ]
        ),
    ],
    className="nav-card"
)

add_class_card = dbc.Card(
    [
        dbc.CardImg(src="assets/add-class-logo.png", top=True, className="card-img d-flex justify-content-center mx-auto"),
        dbc.CardBody(
            [
                html.H4("Add Class", className="card-title d-flex justify-content-center"),
                html.P(
                    "Add new classes or update existing classes' images",
                    className="card-text d-flex justify-content-center",
                ),
                dbc.Button("Add Class Page", color="primary", className="card-nav-button", href='/add-class'),
            ]
        ),
    ],
    className="nav-card"
)

remove_class_card = dbc.Card(
    [
        dbc.CardImg(src="assets/remove-class-logo.png", top=True, className="card-img d-flex justify-content-center mx-auto"),
        dbc.CardBody(
            [
                html.H4("Delete Class", className="card-title d-flex justify-content-center"),
                html.P(
                    "Removal of any existing class inside the system.",
                    className="card-text d-flex justify-content-center",
                ),
                dbc.Button("Remove Class Page", color="primary", className="card-nav-button", href='/remove-class'),
            ]
        ),
    ],
    className="nav-card"
)


navigation_row = dbc.Row(
    [
        dbc.Col(
            classification_card,
            md=True,
            width=4,
        ),
        dbc.Col(
            add_class_card,
            md=True,
            width=4,
        ),
        dbc.Col(
            remove_class_card,
            md=True,
            width=4,
        )
    ],
    no_gutters=True,
    className="d-flex"
)

layout = dbc.Container(
    [
        title_jumbotron,
        info_jumbotron,
        navigation_row
    ],
    fluid=True,
    className="p-0"
)


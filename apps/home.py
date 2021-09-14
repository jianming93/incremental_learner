import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from server import app

title_jumbotron = dbc.Jumbotron(
    [
        dbc.Container(
            [
                html.H1("MITB Incremental Learning", className="display-2 d-flex justify-content-center home-page-header"),
                html.P(
                    "Project by Prof Daniel Lin and Ng Jian Ming",
                    className="lead d-flex justify-content-center home-page-header",
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
                html.Div(
                    [
                        html.H1("About", className="display-5 d-flex info-text-content"),
                        html.P(
                            "The incremental learner aims to explore how to quickly adopt to different "
                            "classes. By using any form of feature extractor for example a Convolutional "
                            "Neural Network (CNN), we can collect these data points to form an entity called shell. "
                            "Every class in this system has this shell which has a centroid based off the mean of "
                            "the features the system has seen before and a 'boundary' based off the median euclidean distance of "
                            "the seen features from this centroid. During inference, the model upon prediction can easily add "
                            "the newly classified image's features to the closest shell it belongs to and perform the same operations "
                            "to update the system. This allows for a scalable system that does not need any computationally intensive "
                            "retraining like traditional machine learning models.",
                            className="lead d-flex info-text-content",
                            id="home-page-content-1"
                        ),
                        html.P(
                            "Currently there are 3 actions performable for this system, namely "
                            "Classification, Add Class and Delete Class. Classification allows "
                            "upload of an image to perform classification. Based on the best score "
                            "(the smallest number shownn in the table) it will assign that uploaded image to the shell " 
                            "and perform the update on the backend. Add Class allows an upload of a zip file. "
                            "This zip file should container a root folder with sub-folders named after the class "
                            "one desires to add to the system where images of the respective classes are present "
                            "in these sub-folders. Lastly, Delete Class removes the class entirely from the system for "
                            "the current system. Likewise, the removal will also occur in the backend.",
                            className="lead d-flex info-text-content",
                            id="home-page-content-2"
                        ),
                        html.P(
                            'Link to the project itself can be found by clicking the button below.',
                            className="lead d-flex info-text-content",
                            id="home-page-content-3"
                        ),
                        dbc.Button(
                            "Go to Github",
                            href="https://github.com/jianming93/incremental_learner",
                            color="primary",
                            className="ml-3 mb-3"
                        )
                    ],
                    id="home-page-info-area",
                ) 
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


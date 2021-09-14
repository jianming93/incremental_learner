from dash_bootstrap_components._components.Col import Col
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from server import app, shell_family
from sql_app.crud import delete_all_shell_images_by_shell_family_id_and_shell_id, delete_shell_for_shell_family
from sql_app.database import SessionLocal, engine


def load_layout():
    help_modal = dbc.Modal(
        [
            dbc.ModalHeader("How to remove class", className="bg-dark text-light"),
            dbc.ModalBody("Select a class from the dropdown below. Once selected, click the Remove class button "
                          "A prompt will ask for confirmation before deletion occurs"),
            dbc.ModalFooter(
                [
                    dbc.Button("Close", id="remove-class-help-modal-close-button", className="ml-auto", color='primary')
                ]
            )
        ],
        id="remove-class-help-modal",
        size="lg"
    )


    modal = dbc.Modal(
        [
            dbc.ModalHeader("Remove class", className="bg-dark text-light"),
            dbc.ModalBody("Are you sure you want to remove these classes? Action is irreversible upon confirmation"),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", id="remove-class-modal-cancel", className="ml-auto", color="secondary"),
                    dbc.Button("Confirm", id="remove-class-modal-confirm", color="primary"),
                ]
            ),
        ],
        id="remove-class-confirmation-modal",
    )


    layout = [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("Remove Class", className="d-flex justify-content-start"),
                    ]
                ),
            ],
            className="pt-2 pb-2"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H5("Select class to remove", className="d-inline justify-content-start"),
                                html.A(
                                    [
                                        html.Img(id="remove-class-help-img", src='assets/question-mark-inside-a-circle-svgrepo-com.svg')
                                    ],
                                    id="remove-class-help-button",
                                    className="d-inline"
                                ),
                            ],
                            className="d-flex justify-content-start"
                        ),
                        dbc.Select(
                            id="remove-class-select-class-to-remove",
                            options=[{"label": i, "value": i} for i in shell_family.classifiers.keys()]
                        )
                    ]
                ),
            ],
            className="pt-2 pb-2"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button("Remove Class", color="primary", className="mr-1", id="remove-class-btn", n_clicks=0),
                    ]
                )
            ],
            className="pt-2 pb-2"
        ),
        modal,
        html.Br(),
        dbc.Alert("Successfully removed class!",
                color="success",
                id="remove-class-success-alert",
                dismissable=True,
                duration=5000,
                is_open=False),
        dbc.Alert("Failed to remove class! Please check inputs or contact administrator!",
                  color="danger",
                  id="remove-class-fail-alert",
                  dismissable=True,
                  duration=5000,
                  is_open=False),
        help_modal,   
    ]

    return layout


@app.callback(
    Output('remove-class-confirmation-modal', 'is_open'),
    [
        Input('remove-class-btn', 'n_clicks'),
        Input('remove-class-modal-confirm', 'n_clicks'),
        Input('remove-class-modal-cancel', 'n_clicks'),
    ],
    [
        State("remove-class-confirmation-modal", "is_open")
    ],
)
def open_confirm_remove_class_modal(n_clicks_remove_class, n_clicks_confirm, n_clicks_cancel, is_open):
    if n_clicks_remove_class or n_clicks_confirm or n_clicks_cancel:
        return not is_open
    return is_open


@app.callback(
    [
        Output('remove-class-success-alert', 'is_open'),
        Output('remove-class-fail-alert', 'is_open'),
        Output('remove-class-select-class-to-remove', 'options')
    ],
    [
        Input('remove-class-modal-confirm', 'n_clicks'),
    ],
    [
        State('remove-class-select-class-to-remove', 'value')
    ]
)
def remove_class(n_click, class_to_remove):
    if n_click > 0:
        try:
            # shell_family.delete_class(class_to_remove)
            # Delete from database
            db = SessionLocal()
            delete_shell_images_results = delete_all_shell_images_by_shell_family_id_and_shell_id(db, shell_family.shell_family_id, class_to_remove)
            delete_shell_results = delete_shell_for_shell_family(db, shell_family.shell_family_id, class_to_remove)
            db.close()
            app.logger.info('Successfully deleted the following class: {}'.format(class_to_remove))
            return True, False, [{"label": i, "value": i} for i in shell_family.classifiers.keys()]
        except Exception as e:
            app.logger.info(e)
            app.logger.info('Error in deleting the following class: {}'.format(class_to_remove))
            return False, True, [{"label": i, "value": i} for i in shell_family.classifiers.keys()]
    else:
        return False, False, [{"label": i, "value": i} for i in shell_family.classifiers.keys()]



@app.callback(
    Output("remove-class-help-modal", "is_open"),
    [Input("remove-class-help-button", "n_clicks"), Input("remove-class-help-modal-close-button", "n_clicks")],
    [State("remove-class-help-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open
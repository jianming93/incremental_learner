import requests

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from server import app, config

def load_layout():
    shell_family_reset_card = dbc.Card(
        dbc.CardBody(
            [
                html.H4("Shell Family Reset", className="card-title"),
                html.P(
                    "Reset current shell_family_id to empty state (no shells present)",
                    className="card-text",
                ),
                dbc.Button("Shell Family Reset", id="admin-shell-family-reset-button", color="primary", n_clicks=0),
            ]
        ),
        style={"width": "18rem"},
    )

    shell_family_reset_success_alert = dbc.Alert(
        "Successfully reset shell_family for shell_family_id: {}".format(config['model']['shell_family_id']),
        id="shell_family_reset_success_alert",
        color="success",
        dismissable=True,
        duration=5000,
        is_open=False
    )

    shell_family_reset_fail_alert = dbc.Alert(
        "Failed reset shell_family for shell_family_id: {}".format(config['model']['shell_family_id']),
        id="shell_family_reset_fail_alert",
        color="danger",
        dismissable=True,
        duration=5000,
        is_open=False
    )


    dummy_container = dbc.Container(
        id="admin-dummy"
    )


    layout = [
        dbc.Row(
            [
                shell_family_reset_card,
            ],
        ),
        shell_family_reset_success_alert,
        shell_family_reset_fail_alert
    ]
    return layout


@app.callback(
    [
        Output('shell_family_reset_success_alert', 'is_open'),
        Output('shell_family_reset_fail_alert', 'is_open'),
    ],
    [
        Input('admin-shell-family-reset-button', 'n_clicks')
    ]
)
def admin_request(shell_family_n_clicks):
    if shell_family_n_clicks > 0:
        response = requests.get(config['dash_environment']['shell_family_reset_api'])
        app.logger.info(response.content)
        if str(respose.status_code) == '200':
            return True, False
        else:
            return False, True
    else:
        return False, True
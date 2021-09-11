import pickle
from collections import OrderedDict

from dash_bootstrap_components._components.NavLink import NavLink
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from src import shell_v2
from server import app, config, shell_family, VALID_USERNAME_PASSWORD_PAIRS
from apps import home, classification, add_class, remove_class, error, admin
from sql_app.database import SessionLocal, engine
from sql_app.crud import get_shell_family_by_shell_family_id, create_shell_family, get_all_shells_by_shell_family_id

def load_auth_layout(pathname):
    if pathname == "/remove-class":
        container_name = 'remove-class'
    elif pathname == "/admin":
        container_name = 'admin'
    else:
        raise ValueError('Incorrect path speicified!')
    username_input = dbc.FormGroup(
        [
            dbc.Label("Username", html_for="auth-username-row", width=2),
            dbc.Col(
                dbc.Input(
                    type="text", id="auth-username-row", placeholder="Enter username"
                ),
                width=10,
            ),
        ],
        row=True,
    )
    password_input = dbc.FormGroup(
        [
            dbc.Label("Password", html_for="auth-password-row", width=2),
            dbc.Col(
                dbc.Input(
                    type="password",
                    id="auth-password-row",
                    placeholder="Enter password",
                ),
                width=10,
            ),
        ],
        row=True,
    )
    modal = dbc.Modal(
        [
            dbc.ModalHeader("Please enter username and password to access this page."),
            dbc.ModalBody(
                [
                    username_input,
                    password_input,
                    dbc.Alert("Invalid username or password! Please try again!",
                              color="danger",
                              id="auth-fail-alert",
                              dismissable=False,
                              is_open=False),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Return to home", id="auth-modal-return-to-home", className="ml-auto", color="secondary", n_clicks=0),
                    dbc.Button("Login", id="auth-modal-login", color="primary"),
                ]
            ),
            
        ],
        id="auth-modal",
        backdrop="static",
        is_open=True,
        size='md'
    )

    layout = [
        modal,
        dbc.Input(id="auth-pathname-input", type="text", value=container_name, className="d-none"),
        dbc.Container(
            id='remove-class-main-container',
            className="pt-3 pb-3",
        ),
        dbc.Container(
            id='admin-main-container',
            className="pt-3 pb-3",
        )
    ]
    return layout

navbar = dbc.NavbarSimple(
    [
        dbc.NavItem(dbc.NavLink("Home", href="/home")),
        dbc.DropdownMenu(
            children=[
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
        dcc.Interval(id="shell-family-update-interval", interval=5000),
        # update_found_toast,
        # update_success_toast,
        # update_failed_toast,
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
        return ("fixed-top", load_auth_layout(pathname), 'page-content mt-5')
    elif pathname == "/admin":
        return ("fixed-top", load_auth_layout(pathname), 'page-content mt-5')
    else:
        return ("fixed-top", error.layout, 'page-content mt-5')


@app.callback(
    [   
        Output('remove-class-main-container', 'children'),
        Output('admin-main-container', 'children'),
        Output('auth-modal', 'is_open'),
        Output('auth-fail-alert', 'is_open')
    ],
    [
        Input('auth-modal-login', 'n_clicks')
    ],
    [
        State('auth-username-row', 'value'),
        State('auth-password-row', 'value'),
        State('auth-pathname-input', 'value')
    ]
)
def auth_verification(n_clicks, username, password, pathname):
    if n_clicks > 0:
        if username in VALID_USERNAME_PASSWORD_PAIRS:
            if password == VALID_USERNAME_PASSWORD_PAIRS[username]:
                if pathname == "remove-class":
                    return remove_class.load_layout(), None, False, False
                elif pathname == "admin":
                    return None, admin.load_layout(), False, False
            else:
                return None, None, True, True
        else:
            return None, None, True, True
    else:
        return None, None, True, False


@app.callback(
    Output('url', 'pathname'),
    [
        Input('auth-modal-return-to-home', 'n_clicks')
    ]
)
def return_to_home_auth(n_clicks):
    if n_clicks > 0:
        return '/home'
    else:
        raise PreventUpdate
        


@app.callback(Output('shell-family-update-interval', 'disabled'),
              [Input('shell-family-update-interval', 'n_intervals')])
def update_shell_family(n_interval):
    db = SessionLocal()
    try:
        app.logger.info('Checking for updates for shell_family_id={}'.format(shell_family.shell_family_id))
        get_shell_family_result = get_shell_family_by_shell_family_id(db, shell_family.shell_family_id)
        if get_shell_family_result.updated_at > shell_family.updated_at:
            app.logger.info('Found update for shell_family_id={} at the following timestamp:{}'.format(shell_family.shell_family_id, get_shell_family_result.updated_at))
            shell_family.feature_extractor_model = get_shell_family_result.feature_extractor_model
            shell_family.create_preprocessor(shell_family.feature_extractor_model)
            shell_family.instances = get_shell_family_result.instances
            shell_family.mapping = get_shell_family_result.mapping
            shell_family.global_mean = (get_shell_family_result.global_mean if get_shell_family_result.global_mean is None else pickle.loads(get_shell_family_result.global_mean))
            shell_family.updated_at = get_shell_family_result.updated_at
            # Extract shells from database baased on shell_family_id
            get_shell_family_shells_database_results = get_all_shells_by_shell_family_id(db, shell_family.shell_family_id)
            if get_shell_family_shells_database_results:
                # Delete all old shells
                shell_family.classifiers = OrderedDict()
                # Get all shell ids and query
                for shell_details in get_shell_family_shells_database_results:
                    shell_family.classifiers[shell_details.shell_id] = shell_v2.ShellModel()
                    shell_family.classifiers[shell_details.shell_id].shell_id = shell_details.shell_id
                    shell_family.classifiers[shell_details.shell_id].shell_mean = (shell_details.shell_mean if shell_details.shell_mean is None else pickle.loads(shell_details.shell_mean))
                    shell_family.classifiers[shell_details.shell_id].num_instances = shell_details.num_instances
                    shell_family.classifiers[shell_details.shell_id].noise_mean = shell_details.noise_mean
                    shell_family.classifiers[shell_details.shell_id].noise_std = shell_details.noise_std
                    shell_family.classifiers[shell_details.shell_id].created_at = shell_details.created_at
                    shell_family.classifiers[shell_details.shell_id].updated_at = shell_details.updated_at
            app.logger.info('Successfully updated shell_family!')
        else:
            app.logger.info('No updates for shell_family_id={}'.format(shell_family.shell_family_id))
    except Exception as e:
        app.logger.info(e)
        app.logger.info('Failed to update shell_family!')
    finally:
        db.close()
        return False


if __name__ == '__main__':
    app.run_server(host=config['dash_environment']['host'],
                   port=config['dash_environment']['port'],
                   debug=config['dash_environment']['debug'])
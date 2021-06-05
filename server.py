import logging
import pickle
import os
# Mute tensorflow logs except for errors as it is flooding the cli
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import yaml
import dash
import dash_bootstrap_components as dbc

from src import shell_v2
from sql_app import crud, models, schemas
from sql_app.database import SessionLocal, engine
from sql_app.crud import get_shell_family_by_shell_family_id, create_shell_family, get_all_shells_by_shell_family_id 

# Connect to database
models.Base.metadata.create_all(bind=engine)

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    prevent_initial_callbacks=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)
server = app.server
app.logger.info('Starting app...')

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

### Create log file handler ###
if not os.path.isfile(config['task_app_environment']['log_filepath']):
    directory_name = os.path.dirname(config['task_app_environment']['log_filepath'])
    if not os.path.isdir(directory_name):
        os.makedirs(directory_name)
    with open(config['task_app_environment']['log_filepath'], 'w') as fp:
        pass
handler = logging.FileHandler(config['dash_environment']['log_filepath'])
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)

app.logger.addHandler(handler)

### Set Environment ###
if config['dash_environment']['use_cpu']:
    app.logger.info("Disabling GPU")
    os.environ["CUDA_VISIBLE_DEVICES"]="-1"
### Load Shell ###
shell_family = shell_v2.ShellFamily()
db = SessionLocal()
if config['model']['shell_family_id'] is None:
    raise ValueError('Please enter an id in config.yaml before stating the application!')

get_shell_family_result = get_shell_family_by_shell_family_id(db, config['model']['shell_family_id'])
if not get_shell_family_result:
    app.logger.info('Input shell_family_id not found! Creating new model with shell_family_id={} and preprocessor={}'.format(config['model']['shell_family_id'], config['model']['feature_extractor_model']))
    app.logger.info('Inserting shell family with shell_family_id={} and feature_extractor_model={} into database'.format(config['model']['shell_family_id'], config['model']['feature_extractor_model']))
    shell_family_database_entry = create_shell_family(db,
                                                      config['model']['shell_family_id'],
                                                      config['model']['feature_extractor_model'],
                                                      shell_family.instances,
                                                      shell_family.mapping,
                                                      shell_family.global_mean)
    get_shell_family_result = get_shell_family_by_shell_family_id(db, config['model']['shell_family_id'])
else:
    app.logger.info('Found saved shell family with shell_family_id: {}'.format(config['model']['shell_family_id']))
    app.logger.info('Loading model with shell_family_id: {}'.format(config['model']['shell_family_id']))
shell_family.shell_family_id = get_shell_family_result.shell_family_id
shell_family.feature_extractor_model = get_shell_family_result.feature_extractor_model
shell_family.create_preprocessor(shell_family.feature_extractor_model)
shell_family.instances = get_shell_family_result.instances
shell_family.mapping = get_shell_family_result.mapping
shell_family.global_mean = (get_shell_family_result.global_mean if get_shell_family_result.global_mean is None else pickle.loads(get_shell_family_result.global_mean))
shell_family.updated_at = get_shell_family_result.updated_at
# Extract shells from database baased on shell_family_id
get_shell_family_shells_database_results = get_all_shells_by_shell_family_id(db, config['model']['shell_family_id'])
if get_shell_family_shells_database_results:
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
app.logger.info('Model Loaded!')
# Close database
db.close()

app.logger.info('App is ready to use!')
app.logger.info('')
# Log config summary
summary_string = '* Config Summary *\n'
for config_key in config:
    summary_string += '=' * (len(config_key) + 4)
    summary_string += '\n'
    summary_string += '= ' + config_key + ' ='
    summary_string += '\n'
    summary_string += '=' * (len(config_key) + 4)
    summary_string += '\n'
    for parameter in config[config_key]:
        summary_string += '{}: {}'.format(parameter, config[config_key][parameter])
        summary_string += '\n'
app.logger.info(summary_string)

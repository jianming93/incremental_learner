import logging
import os
# Mute tensorflow logs except for errors as it is flooding the cli
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import yaml
import dash
import dash_bootstrap_components as dbc

from src import shell

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

### Set Environment ###
if config['environment']['use_cpu']:
    app.logger.info("Disabling GPU")
    os.environ["CUDA_VISIBLE_DEVICES"]="-1"
### Load Shell ###
shell_family = shell.ShellFamily()
if config['model']['model_path'] is None:
    app.logger.info('Creating new model with the following preprocessor: {}'.format(config['model']['feature_extractor_model']))
    shell_family.create_preprocessor(config['model']['feature_extractor_model'])
else:
    if os.path.exists(config['model']['model_path']):
        app.logger.info('Found saved shell family with filepath: {}'.format(config['model']['model_path']))
        app.logger.info('Loading new model with filepath: {}'.format(config['model']['model_path']))

        shell_family.load(config['model']['model_path'])
        app.logger.info('Model Loaded!')
    else:
        app.logger.info('Incorrect filepath specified! Loading model with the following preprocessor: {}'.format(config['model']['feature_extractor_model']))
        shell_family.create_preprocessor(config['model']['feature_extractor_model'])
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

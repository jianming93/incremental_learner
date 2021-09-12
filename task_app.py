import atexit
import logging
import datetime
import pickle
import os
# Mute tensorflow logs except for errors as it is flooding the cli
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
import yaml
import numpy as np
import tensorflow as tf

from src.shell_v2 import ShellModel, ShellFamily
from sql_app import models, schemas
from sql_app.database import SessionLocal, engine
from sql_app.crud import (get_shell_families,
                          get_shell_family_by_shell_family_id,
                          create_shell_family,
                          get_all_shells_by_shell_family_id,
                          get_all_shell_images_by_shell_family_id_and_shell_id,
                          get_latest_shell_image_by_shell_family_id,
                          get_latest_shell_image_by_shell_family_id_and_shell_id,
                          get_all_shell_images_by_shell_family_id_and_shell_id_with_no_image_features,
                          update_shell_family,
                          update_shell_for_shell_family,
                          update_all_shell_images_by_shell_family_id_and_shell_id_with_no_image_features,
                          delete_shell_family,
                          delete_shell_for_shell_family,
                          delete_all_shell_images_by_shell_family_id_and_shell_id,
                          delete_image)
### State dict to determine what operation to perform ###
# State is to indicate what the task_app is doing.
# changes_found is to indicate if during update in progress or reset in progress, a change is detected
# this is because there are times where update is in progress for the task_app but no changes are found
# which means shell_family's state has no updates.
STATE_DICT = {"state": "update", "changes_found": False}
### Load Config ###
with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
### Set Logging Level ###
logging.basicConfig(level=logging.DEBUG)
### Create log file handler ###
if not os.path.isfile(config['task_app_environment']['log_filepath']):
    directory_name = os.path.dirname(config['task_app_environment']['log_filepath'])
    if not os.path.isdir(directory_name):
        os.makedirs(directory_name)
    with open(config['task_app_environment']['log_filepath'], 'w') as fp:
        pass
handler = logging.FileHandler(config['task_app_environment']['log_filepath'])
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)

def perform_task_by_state():
    if STATE_DICT['state'] == "shell_family_reset":
        STATE_DICT['state'] = "shell_family_reset_in_progress"
        reset_shell_family_database_state()
        # Always reset back to update state after triggering any kind of reset
        STATE_DICT['state'] = "update"
    elif STATE_DICT['state'] == "shell_family_reset_in_progress":
        # Log as information to indicate reset is already ongoing
        app.logger.info('Shell Family reset already in progress!')
    elif STATE_DICT['state'] == "full_reset":
        STATE_DICT['state'] = "full_reset_in_progress"
        full_reset_database_state()
        # Always reset back to update state after triggering any kind of reset
        STATE_DICT['state'] = "update"
    elif STATE_DICT['state'] == "full_reset_in_progress":
        # Log as information to indicate reset is already ongoing
        app.logger.info('Full reset already in progress!')
    elif STATE_DICT['state'] == "update":
        STATE_DICT['state'] = "update_in_progress"
        update_shells_in_database()
        STATE_DICT['state'] = "update"
    elif STATE_DICT['state'] == "update_in_progress":
        app.logger.info('Shell Family update already in progress!')



def reset_shell_family_database_state():
    db = SessionLocal()
    try:
        app.logger.info('Full reset triggered! Resetting all tables and recreating empty shell family for shell_family_id={}'.format(config['model']['shell_family_id']))
        all_shells_for_shell_family_id = get_all_shells_by_shell_family_id(db, config['model']['shell_family_id'])
        for shell_details in all_shells_for_shell_family_id:
            shell = shell_details.shell_id
            delete_all_shell_images_by_shell_family_id_and_shell_id(db, config['model']['shell_family_id'], shell)
            delete_shell_for_shell_family(db, config['model']['shell_family_id'], shell)
        delete_shell_family(db, config['model']['shell_family_id'])
        app.logger.info('Successfully deleted all shells and records for shell_family_id: {}'.format(config['model']['shell_family_id']))
        # Recreate new learner with id same as previous
        app.logger.info('Recreating shell family as new record for shell_family_id: {}'.format(config['model']['shell_family_id']))
        recreated_shell_family = ShellFamily()
        shell_family_database_entry = create_shell_family(db,
                                                          config['model']['shell_family_id'],
                                                          config['model']['feature_extractor_model'],
                                                          recreated_shell_family.instances,
                                                          recreated_shell_family.mapping,
                                                          recreated_shell_family.global_mean)
        app.logger.info('Successfully recreated shell family as new record for shell_family_id: {}'.format(config['model']['shell_family_id']))
        app.logger.info('Successfully executed shell family reset!')
    except Exception as e:
        app.logger.info(e)
        app.logger.info('Shell family reset has failed!')
    finally:
        db.close()


def full_reset_database_state():
    ### TODO: Create a full reset function ###
    pass
    # db = SessionLocal()
    # try:
    #     app.logger.info('Shell family reset triggered! Starting reset for shell_family_id: {}'.format(config['model']['shell_family_id']))
    #     all_shells_for_shell_family_id = get_all_shells_by_shell_family_id(db, config['model']['shell_family_id'])
    #     for shell_details in all_shells_for_shell_family_id:
    #         shell = shell_details.shell_id
    #         delete_all_shell_images_by_shell_family_id_and_shell_id(db, config['model']['shell_family_id'], shell)
    #         delete_shell_for_shell_family(db, config['model']['shell_family_id'], shell)
    #     delete_shell_family(db, config['model']['shell_family_id'])
    #     app.logger.info('Successfully deleted all shells and records for shell_family_id: {}'.format(config['model']['shell_family_id']))
    #     # Recreate new learner with id same as previous
    #     app.logger.info('Recreating shell family as new record for shell_family_id: {}'.format(config['model']['shell_family_id']))
    #     recreated_shell_family = ShellFamily()
    #     shell_family_database_entry = create_shell_family(db,
    #                                                       config['model']['shell_family_id'],
    #                                                       config['model']['feature_extractor_model'],
    #                                                       recreated_shell_family.instances,
    #                                                       recreated_shell_family.mapping,
    #                                                       recreated_shell_family.global_mean)
    #     app.logger.info('Successfully recreated shell family as new record for shell_family_id: {}'.format(config['model']['shell_family_id']))
    #     app.logger.info('Successfully executed shell family reset!')
    # except Exception as e:
    #     app.logger.info(e)
    #     app.logger.info('Shell family reset has failed!')
    # finally:
    #     db.close()


def update_shells_in_database():
    db = SessionLocal()
    try:
        app.logger.info('Update Triggered! Starting Update')
        # Step 1: Get all shell_family_id existing in database
        all_shell_families_results = get_shell_families(db)
        if all_shell_families_results:
            for shell_family_details in all_shell_families_results:
                app.logger.info('Checking Shell Family with shell_family_id={} for updates'.format(shell_family_details.shell_family_id))
                app.logger.info('Instantiating Shell Family with shell_family_id={}'.format(shell_family_details.shell_family_id))
                shell_family = ShellFamily()    
                # Step 2: Load current shell family configuration
                shell_family.shell_family_id = shell_family_details.shell_family_id
                shell_family.instances = shell_family_details.instances
                shell_family.mapping = shell_family_details.mapping
                shell_family.created_at = shell_family_details.updated_at
                shell_family.updated_at = shell_family_details.updated_at
                shell_family.create_preprocessor(shell_family_details.feature_extractor_model)
                app.logger.info('Successfully instantiate Shell Family with shell_family_id={}'.format(shell_family_details.shell_family_id))
                # Step 3: Get all shells for shell family
                app.logger.info('Retrieving all shells for Shell Family with shell_family_id={}'.format(shell_family_details.shell_family_id))
                all_shells_result = get_all_shells_by_shell_family_id(db, shell_family.shell_family_id)
                if all_shells_result:
                    app.logger.info('Successfully retrieved shells for Shell Family with shell_family_id={}'.format(shell_family_details.shell_family_id))
                # Step 3.1: Create variable to store all features for global mean recalculation and
                # to help with tracking and for further calculations
                shell_family_features = np.array([])
                shell_has_updated = False
                shell_has_been_deleted = False
                shell_image_classes = []
                app.logger.info('Checking retrieved shells for updates for Shell Family with shell_family_id={}'.format(shell_family_details.shell_family_id))
                for shell_details in all_shells_result:
                    # Step 4: Load shell configuration
                    app.logger.info('Loading shell_id={} for Shell Family with shell_family_id={}'.format(shell_details.shell_id, shell_family_details.shell_family_id))
                    shell_family.classifiers[shell_details.shell_id] = ShellModel()
                    shell_family.classifiers[shell_details.shell_id].shell_id = shell_details.shell_id
                    shell_image_classes.append(shell_details.shell_id)
                    # Shell Mean needs a pickle load due to binary storage of numpy array
                    shell_family.classifiers[shell_details.shell_id].shell_mean = (shell_details.shell_mean if shell_details.shell_mean is None else pickle.loads(shell_details.shell_mean))
                    shell_family.classifiers[shell_details.shell_id].num_instances = shell_details.num_instances
                    shell_family.classifiers[shell_details.shell_id].noise_mean = shell_details.noise_mean
                    shell_family.classifiers[shell_details.shell_id].noise_std = shell_details.noise_std
                    shell_family.classifiers[shell_details.shell_id].created_at = shell_details.created_at
                    shell_family.classifiers[shell_details.shell_id].updated_at = shell_details.updated_at
                    app.logger.info('shell_id={} successfully loaded for Shell Family with shell_family_id={}'.format(shell_details.shell_id, shell_family_details.shell_family_id))
                    # Step 5: Check if class has any newly updated images by checking null in image_features column
                    null_shell_images_results = get_all_shell_images_by_shell_family_id_and_shell_id_with_no_image_features(db, shell_family.shell_family_id, shell_details.shell_id)
                    if null_shell_images_results:
                        app.logger.info('Found new images for shell_id={} for Shell Family with shell_family_id={}'.format(shell_details.shell_id, shell_family_details.shell_family_id))
                        # Step 5.5: Update STATE_DICT to indicate changes found
                        if not STATE_DICT['changes_found']:
                            STATE_DICT['changes_found'] = True
                        # Step 6: Update all images with no image features with regards to shell_family_id and shell_id
                        update_datetime = datetime.datetime.utcnow()
                        shell_has_updated = True
                        update_shell_images_results =\
                            update_all_shell_images_by_shell_family_id_and_shell_id_with_no_image_features(db,
                                                                                                           shell_family.shell_family_id,
                                                                                                           shell_details.shell_id,
                                                                                                           shell_family,
                                                                                                           config['model']['batch_size'],
                                                                                                           config['model']['target_size'],
                                                                                                           update_datetime)
                    # Step 7: Perform additional check to see if classification module has updates to database
                    # This is done by checking for latest timestamp to determine if there is an update
                    latest_shell_image_for_current_shell_result = get_latest_shell_image_by_shell_family_id_and_shell_id(db, shell_family.shell_family_id, shell_details.shell_id)
                    if latest_shell_image_for_current_shell_result.assigned_at > shell_family.updated_at:
                        shell_has_updated = True
                    # Step 8: Get all shell images to append to shell_family_features
                    app.logger.info('Adding features from shell_id={} to Shell Family raw_features attribute with shell_family_id={}'.format(shell_details.shell_id, shell_family_details.shell_family_id))
                    all_images_for_shell_family_and_current_shell_results =\
                        get_all_shell_images_by_shell_family_id_and_shell_id(db, shell_family.shell_family_id, shell_details.shell_id)
                    shell_features = [pickle.loads(shell_image_details.image_features) for shell_image_details in all_images_for_shell_family_and_current_shell_results]
                    if shell_family_features.shape[0] == 0:
                        shell_family_features = np.array(shell_features)
                    else:
                        shell_family_features = np.concatenate(
                            [
                                shell_family_features,
                                shell_features
                            ],
                            axis=0,
                        )
                    # Assign to raw features for potential calculations
                    shell_family.classifiers[shell_details.shell_id].raw_features = np.array(shell_features)
                # Step 9: Perform additional check to see if a class has been removed from the database
                # This is done by checking if the shell_family's mapping matches the shell classes present in the shell images
                shell_image_classes.sort()
                shell_family_classes = list(shell_family.mapping)
                shell_family_classes.sort()
                if shell_image_classes != shell_family_classes:
                    # Step 9.5: Update STATE_DICT to indicate changes found
                    if not STATE_DICT['changes_found']:
                        STATE_DICT['changes_found'] = True
                    shell_has_updated = True
                    shell_has_been_deleted = True
                    update_datetime = datetime.datetime.utcnow()
                    for shell_class in shell_image_classes:
                        shell_family.classifiers[shell_class].updated_at = update_datetime
                # Step 10: Update shell_family and shells if needed
                if (shell_has_updated):
                    app.logger.info('Retrieved last uploaded image timestamp for shell_family_id={}'.format(shell_family_details.shell_family_id))
                    latest_shell_image_result = get_latest_shell_image_by_shell_family_id(db, shell_family_details.shell_family_id)
                    if not shell_has_been_deleted:
                        update_datetime = latest_shell_image_result.assigned_at
                    app.logger.info('Updating Shell Family parameter as update was found in its shells for shell_family_id={}'.format(shell_family_details.shell_family_id))
                    # Step 10.1: Update shell_family global mean
                    new_global_mean = np.mean(shell_family_features, axis=0, keepdims=True)
                    shell_family.global_mean = new_global_mean
                    shell_family.instances =  shell_family_features.shape[0]
                    shell_family.mapping = list(shell_family.classifiers.keys())
                    shell_family.updated_at = update_datetime
                    update_shell_family_results = update_shell_family(db,
                                                                    shell_family.shell_family_id,
                                                                    shell_family.feature_extractor_model,
                                                                    int(shell_family.instances),
                                                                    shell_family.mapping,
                                                                    pickle.dumps(shell_family.global_mean),
                                                                    update_datetime)
                    # Step 10.2: Update all shells
                    app.logger.info("Updating all Shells' parameters in Shell Family for shell_family_id={}".format(shell_family_details.shell_family_id))
                    shell_family.update_shells(new_global_mean)
                    for shell_class in shell_family.classifiers:
                        shell_family.classifiers[shell_class].updated_at = update_datetime
                        update_shell_results = update_shell_for_shell_family(db,
                                                                            shell_family.shell_family_id,
                                                                            shell_class,
                                                                            pickle.dumps(shell_family.classifiers[shell_class].shell_mean),
                                                                            int(shell_family.classifiers[shell_class].num_instances),
                                                                            float(shell_family.classifiers[shell_class].noise_mean),
                                                                            float(shell_family.classifiers[shell_class].noise_std),
                                                                            shell_family.classifiers[shell_class].updated_at)
                    app.logger.info('Successfully updated Shell Family with shell_family_id={}'.format(shell_family_details.shell_family_id))
                else:
                    app.logger.info('Nothing to update for shell family with shell_family_id={}'.format(shell_family_details.shell_family_id))
        else:
            app.logger.info('No Shell Family found!')
    except Exception as e:
        app.logger.info(e)
        app.logger.info('Update has failed!')
    finally:
        db.close()
        tf.keras.backend.clear_session()
        # Reset STATE_DICT changes found to be back to False
        STATE_DICT['changes_found'] = False


job_defaults = {
    'coalesce': config['task_app_environment']['coalesce'],
    'max_instances': config['task_app_environment']['max_instances']
}


### Create Scheduler ###
sched = BackgroundScheduler(daemon=True, job_defaults=job_defaults)
### Add jobs for scheduler ###
sched.add_job(perform_task_by_state,'interval', seconds=config['task_app_environment']['seconds_interval'])
### Start Scheduler ###
sched.start()

app = Flask(__name__)
app.logger.addHandler(handler)

@app.route("/test", methods=["GET"])
def test():
    """ Function for test purposes. """
    return "This is a test response"

@app.route('/shell_family_reset', methods=["GET"])
def set_shell_family_reset_state():
    STATE_DICT['state'] = 'shell_family_reset'
    return "Shell family reset request successful!"

@app.route('/state', methods=["GET"])
def get_state():
    return STATE_DICT

atexit.register(lambda: sched.shutdown(wait=False))

if __name__ == "__main__":
    app.run(host=config['task_app_environment']['host'],
            port=config['task_app_environment']['port'],
            debug=config['task_app_environment']['debug'])
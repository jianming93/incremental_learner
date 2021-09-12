import os
import shutil
import io
import base64
import pickle
from zipfile import ZipFile

from dash_bootstrap_components._components.Col import Col
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_table
import tqdm
import numpy as np

from server import app, shell_family, config
from src.utils import ImageGenerator
from sql_app.crud import get_all_shells_by_shell_family_id, bulk_create_images, bulk_create_shell_images_for_one_shell_family, create_shell_for_shell_family
from sql_app.database import SessionLocal, engine


help_modal = dbc.Modal(
    [
        dbc.ModalHeader("How to add class"),
        dbc.ModalBody("Upload a zip file containing all the images of the class desired to be part of the model's dataset. "
                      "Verify the correct number of images below before clicking the button at the bottom."),
        dbc.ModalFooter(
            [
                dbc.Button("Close", id="add-class-help-modal-close-button", className="ml-auto", color='primary')
            ]
        )
    ],
    id="add-class-help-modal",
)


layout = dbc.Container(
    [   
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("Add New Class", className="d-flex justify-content-start"),
                    ]
                ),
            ],
            className="pt-2 pb-2"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Upload zip file of new classes images",
                                className="d-inline justify-content-start"),
                        html.A(
                            [
                                html.Img(id="add-class-help-img", src='assets/question-mark-inside-a-circle-svgrepo-com.svg')
                            ],
                            id="add-class-help-button",
                            className="d-inline"
                        )
                    ]
                )    
            ],
            className="pt-2 pb-2"       
        ),
        dbc.Row(
            [
                dcc.Upload(
                    id="add-class-upload-image-area",
                    children=
                    [
                        html.Div(
                            [
                                html.A("Drag and Drop or Select Zip File")
                            ]
                        )
                    ],
                )
            ],
            className="pt-2 pb-2"
        ),
        dcc.Loading(
            dbc.Alert("Successfully Uploaded",
                      id='add-class-success-alert',
                      color="success",
                      dismissable=True,
                      duration=5000,
                      is_open=False),
            fullscreen=True,
            type='default',
            parent_className ="loader"
        ),
        dbc.Alert("Upload has failed! Please check inputs!",
                  id='add-class-fail-alert',
                  color="danger",
                  dismissable=True,
                  duration=5000,
                  is_open=False),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5('Uploaded zip file summary')
                    ]
                ),
            ],
            className="pt-2 pb-2"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(
                            dash_table.DataTable(
                                id='add-class-table',
                                columns=[{"name": "Class Name", "id": "class-name-column"},
                                         {"name": "Number of images", "id": "number-of-images-column"},
                                         {"name": "Existing Class", "id": "existing-class-column"},],
                            ),
                            id='add-class-table-loader',
                            type='default',
                            parent_className ="loader"
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
                        dbc.Button("Add New Classes", id="add-class-button", color="primary", className="mr-1", n_clicks=0),
                    ],
                    className="p-0"
                )
            ],
            className="pt-2 pb-2"
        ),
        html.Br(),
        help_modal,
        
    ], 
    id="add-class-main-container",
    className="pt-3 pb-3",
)


@app.callback(
    Output('add-class-table', 'data'),
    [
        Input('add-class-upload-image-area', 'contents')
    ],
    [
        State('add-class-upload-image-area', 'filename'),
        State('add-class-upload-image-area', 'last_modified')
    ]
)
def generate_uploaded_zip_file_summary(content, name, date):
    if content is not None and name.endswith('.zip'):
        # the content needs to be split. It contains the type and the real content
        content_type, content_string = content.split(',')
        # Decode the base64 string
        content_decoded = base64.b64decode(content_string)
        # Use BytesIO to handle the decoded content
        zip_str = io.BytesIO(content_decoded)
        # Now you can use ZipFile to take the BytesIO output
        zip_obj = ZipFile(zip_str, 'r')
        classes_folder_list = [x for x in zip_obj.namelist() if x.endswith('/')][1:]
        # Populate table
        current_classes_in_model = os.listdir(config['dash_environment']['save_image_directory'])
        file_counter = []
        for folder in classes_folder_list:
            file_counter.append({"class-name-column": folder.split('/')[1],
                                 "number-of-images-column": len([x for x in zip_obj.namelist() if x.startswith(folder)]),
                                 "existing-class-column": folder in current_classes_in_model})
        zip_obj.close()
        return file_counter


@app.callback(
    [
        Output('add-class-success-alert', 'is_open'),
        Output('add-class-fail-alert', 'is_open'),
    ],
    [
        Input('add-class-button', 'n_clicks')
    ],
    [
        State('add-class-upload-image-area', 'contents'),
        State('add-class-upload-image-area', 'filename'),
        State('add-class-upload-image-area', 'last_modified')
    ]
)
def add_class_to_model(n_clicks, content, name, date):
    if n_clicks > 0:
        try:
            # the content needs to be split. It contains the type and the real content
            content_type, content_string = content.split(',')
            # Decode the base64 string
            content_decoded = base64.b64decode(content_string)
            # Use BytesIO to handle the decoded content
            zip_str = io.BytesIO(content_decoded)
            # Now you can use ZipFile to take the BytesIO output
            zip_obj = ZipFile(zip_str, 'r')
            # Extract files
            classes_folder_list = [x for x in zip_obj.namelist() if x.endswith('/')][1:]
            current_classes_in_model = os.listdir(config['dash_environment']['save_image_directory'])
            # Need class_name_array, class_index_array and image_path_array
            # class_name_array stores the unique classes present
            # class_index_array stores the class index for each image. Index goes by the class folder list
            # image_path_array stores the image path after copying to the backend which is determined
            # by config['dash_environment']['save_image_directory']
            unique_class_name_array = []
            class_index_array = []
            class_name_array = []
            image_path_array = []
            for i in range(len(classes_folder_list)): 
                folder = classes_folder_list[i]
                class_name = folder.split('/')[1]
                class_name = class_name.lower()
                if class_name not in current_classes_in_model:
                    os.mkdir(os.path.join(config['dash_environment']['save_image_directory'], class_name))
                if class_name not in unique_class_name_array:
                    unique_class_name_array.append(class_name)
                save_path = os.path.join(config['dash_environment']['save_image_directory'], class_name)
                all_class_image_paths = [x for x in zip_obj.namelist() if x.startswith(folder)][1:]
                for class_image_path in all_class_image_paths:
                    class_filename = os.path.basename(class_image_path)
                    with open(os.path.join(save_path, class_filename), 'wb') as save_image_file:
                        save_image_file.write(zip_obj.read(class_image_path))
                    image_path_array.append(os.path.join(save_path, class_filename))
                    class_index_array.append(i)
                    class_name_array.append(class_name)
            # all_dataset_image_features = np.array([])
            # all_image_paths = []
            # all_classes = []
            # Use image_path_array and class_index_array for image generator
            # Create image generator
            # image_generator = ImageGenerator(image_path_array, class_index_array, config['model']['batch_size'], (config['model']['target_size'], config['model']['target_size']))
            # for (batch_images, batch_filepaths, batch_classes) in tqdm.tqdm(image_generator, total=int(np.ceil(len(image_generator) / config['model']['batch_size']))):
            #     features = shell_family.preprocessor.predict(batch_images)
            #     if all_dataset_image_features.shape[0] == 0:
            #         all_dataset_image_features = np.array(features)
            #     else:
            #         all_dataset_image_features = np.concatenate(
            #             [
            #                 all_dataset_image_features,
            #                 features
            #             ],
            #             axis=0,
            #         )
            #     all_image_paths += list(batch_filepaths)
            #     all_classes += [unique_class_name_array[i] for i in batch_classes]
            # shell_family.fit(image_generator, unique_class_name_array, config['model']['model_path'])
            # Save to database
            app.logger.info('Adding new classes/existing classes images and metadata to database..')
            db = SessionLocal()
            # Add images to database
            create_images_result = bulk_create_images(db, class_name_array, image_path_array)
            # Check for current shells existing in shell family
            all_shells_for_shell_family_id_result = get_all_shells_by_shell_family_id(db, shell_family.shell_family_id)
            # Remove overlaps if present
            if len(all_shells_for_shell_family_id_result) == 0:
                class_to_add = unique_class_name_array
            else:
                database_shell_ids = [all_shells_for_shell_family_id_result[i].shell_id for i in range(len(all_shells_for_shell_family_id_result))]
                # Find difference to add to database
                class_to_add = list(set(unique_class_name_array).difference(database_shell_ids))
                app.logger.info('Found following new shells to add to database: {}'.format(class_to_add))
            # Add shell ids to database
            for new_class in class_to_add:
                create_shell_for_shell_family(db, config['model']['shell_family_id'], new_class, None, None, None, None)
            # Assign images to shell fmaily and shell id 
            assign_to_shell_family_and_shells_result = bulk_create_shell_images_for_one_shell_family(db, shell_family.shell_family_id, class_name_array, image_path_array, [None for i in range(len(image_path_array))])
            db.close()
            app.logger.info('Successfully added to database!') 
            # Close zip file when done
            zip_obj.close()
            app.logger.info('Successfully added/updated new images with the following classes: {}'.format(unique_class_name_array))
            return True, False
        except Exception as e:
            app.logger.info(e)
            app.logger.info('Error in adding new classes!')
            return False, True
    else:
        return False, False


@app.callback(
    Output("add-class-help-modal", "is_open"),
    [Input("add-class-help-button", "n_clicks"), Input("add-class-help-modal-close-button", "n_clicks")],
    [State("add-class-help-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open
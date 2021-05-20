import io
import base64
from PIL import Image

import numpy as np
from dash_bootstrap_components._components.Col import Col
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from dash.dependencies import Input, Output, State

from server import app, shell_family, config


help_modal = dbc.Modal(
    [
        dbc.ModalHeader("How to perform classification"),
        dbc.ModalBody("Upload an image in the upload area. Image will be displayed on the left. "
                      "Results for the classification (which is a distance metric) will be displayed "
                      "on the right side sorted by the closest match."),
        dbc.ModalFooter(
            [
                dbc.Button("Close", id="classification-help-modal-close-button", className="ml-auto", color='primary')
            ]
        )
    ],
    id="classification-help-modal",
)


layout = dbc.Container(
    [   
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("Classification", className="d-flex justify-content-start"),
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
                                html.H5("Upload image to perform classification", className="d-inline justify-content-start"),
                                html.A(
                                    [
                                        html.Img(id="classification-help-img", src='assets/question-mark-inside-a-circle-svgrepo-com.svg')
                                    ],
                                    id="classification-help-button",
                                    className="d-inline"
                                ),
                            ],
                            className="d-flex justify-content-start"
                        ),
                        dcc.Upload(
                            id="classification-upload-image-area",
                            children=
                            [
                                html.Div(
                                    [
                                        html.A("Drag and Drop or Select File")
                                    ]
                                )
                            ]
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
                        html.H5("Uploaded Image", className="d-flex justify-content-start"),
                        dcc.Loading(
                            html.Img(src="", id="classification-upload-image"),
                            id="classification-upload-image-loader",
                            type="default",
                            parent_className="loader"
                        ),
                        
                    ]
                ),
                dbc.Col(
                    [
                        html.H5("Class Match Distance", className="d-flex justify-content-start"),
                        dcc.Loading(
                            dash_table.DataTable(
                                id='classification-output-results-table',
                                columns=[{"name": "Class Name", "id": "class-name-column"},
                                        {"name": "Distance", "id": "distance-column"}],
                            ),
                            id="classification-output-results-table-loader",
                            type="default",
                            parent_className="loader"
                        ),
                    ]
                ),
            ],
            className="pt-2 pb-2"
        ),
        dbc.Alert("There was an issue uploading/classifying image! Please check input or contact administrator!",
                  color="danger",
                  id="classification-fail-alert",
                  dismissable=True,
                  duration=5000,
                  is_open=False),
        help_modal,
        
    ], 
    id="add-class-main-container",
    className="pt-3 pb-3",
)



@app.callback(
    [Output('classification-upload-image', 'src'),
     Output('classification-output-results-table', 'data'),
     Output('classification-fail-alert', 'is_open')],
    [
        Input('classification-upload-image-area', 'contents')
    ],
    [
        State('classification-upload-image-area', 'filename'),
        State('classification-upload-image-area', 'last_modified')
    ]
)
def generate_uploaded_zip_file_summary(content, name, date):
    if content is not None:
        try:
            file_extension = name.split('.')[1]
            # Split away meta data (i.e. 'data:image/png;base64,...base 64 stuff....')
            decoded_content = base64.b64decode(content.split(',')[1])
            img_buf = io.BytesIO(decoded_content)
            # Loading into PIL Image
            img = Image.open(img_buf).convert("RGB")
            # Resize by size used for model
            resized_img = img.resize((config['model']['target_size'], config['model']['target_size']))
            img_array = np.array(resized_img)
            # Expand dims due to keras model including batch dimensions
            img_array = np.expand_dims(resized_img, 0)
            # Preprocess with keras' preprocess_input based on the respective model architecture
            preprocessed_img_array = shell_family.preprocessor_preprocess_function(img_array)
            # Generate features
            sample_features = shell_family.preprocessor.predict(preprocessed_img_array)
            # Perform classification
            class_index, class_name, score, full_results = shell_family.score(sample_features, 0.5, with_update=False, return_full_results=True)
            # Sort results
            full_class_names = np.array(list(full_results.keys()))
            full_scores_list = np.array([i[0] for i in full_results.values()])
            sorted_index_list = np.argsort(full_scores_list)
            # Reverse sorting since negative sign used to determine closest match
            sorted_index_list = sorted_index_list[::-1]
            sorted_class_names = full_class_names[sorted_index_list]
            sorted_scores_list = full_scores_list[sorted_index_list]
            output_results = []
            for class_name, distance in zip(sorted_class_names, sorted_scores_list):
                output_results.append({'class-name-column': class_name, 'distance-column': abs(distance)})
            ### TODO: Add thresholding and model updates here ###
            app.logger.info('Successfully perform classification!')
            return content, output_results, False
        except:
            app.logger.info('Error in performing classification!')
            return None, None, True
    else:
        return None, None, False


@app.callback(
    Output("classification-help-modal", "is_open"),
    [Input("classification-help-button", "n_clicks"), Input("classification-help-modal-close-button", "n_clicks")],
    [State("classification-help-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open
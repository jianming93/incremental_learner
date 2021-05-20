# MITB Incremental Learner Capstone Project

## 1. Overview
This is a project from SMU MITB to build an incremental learner system. The idea is to have a system where it can be quickly updated and also be expanded upon the original classes easily.


## 2. How to run
1. Edit the config in the **config.yaml** file based. The description of each config field are as follows:

environment:
  - host: IP Address to host the dash application.
  - port: Port to serve the dash application. Note that    the port defined here will need to match the docker's port specified later when running the docker.
  - debug: To run dash application in debug mode.
  - use_cpu: To expose GPU or not for tensorflow's model inference.
  - save_image_directory: Location to store uploaded images

model:
  - model_path: Filepath to the incremental learner model. If does not exist, a pickle file will be created with the filepath specified upon the first addition of classes.
  - feature_extractor_model: The model architecture used to generate the features for the incremental learner. Can only be **resnet50**, **vgg16** or **mobilenet**.
  - batch_size: Batch size to perform inference for the feature extractor model.
  - target_size: Image size to be resized to.
  - threshold: Threshold to consider a correct classification. This is a distance metric threshold not a probabilistic one.

2. Build the docker at the root folder with the following command:
```
docker build -t <name_of_image> .
```
Replace **<name_of_image>** with the name you desire to specify for the docker image.

3. Run the docker with the following command:
```
docker run -p <host_port>:<application_port> --name <name_of_container> <name_of_image>
```
Similar to above, replace **<name_of_image>** and **<name_of_container>** with your desired name for the docker. For **<host_port>** and **<application_port>**, do note the **<application_port>** has to match the port specified in **config.yaml**. **<host_port>** can be any port you desire to access to from the browser.

4. Open the application in your localhost via the following link:
```
localhost:<host_port>
```
You should be able to see the home page of the incremental learner application.
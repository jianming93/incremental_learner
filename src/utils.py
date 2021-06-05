import os
import shutil 
import glob
from random import sample 
import timeit
from PIL import Image

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.metrics import average_precision_score
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.applications import MobileNet
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import GlobalAvgPool2D, GlobalMaxPool2D

########################
# ImageGenerator Class #
########################
class ImageGenerator():
    def __init__(self, filepath_array, class_array, batch_size, target_size):
        self.filepath_array = filepath_array
        self.class_array = class_array
        self.batch_size = batch_size
        self.target_size = target_size
        self.steps = len(self.class_array) // self.batch_size
        self.index = 0
        print("Found {} images with {} classes!".format(self.__len__(), len(np.unique(self.class_array))))
    
    def __iter__(self):
        return self
    
    def __len__(self):
        assert(len(self.class_array) == len(self.filepath_array))
        return len(self.class_array)
    
    def __next__(self):
        if self.index == self.__len__():
            raise StopIteration
        elif self.index + self.batch_size >= self.__len__():
            batch_filepaths = np.array(self.filepath_array[self.index : self.__len__()])
            batch_images = np.array([np.asarray(Image.open(i).convert("RGB").resize(self.target_size))[..., :3] for i in batch_filepaths]).astype(np.float32)
            batch_images = preprocess_input(batch_images)
            batch_classes = self.class_array[self.index : self.__len__()]
            self.index = self.__len__()
            return (batch_images, batch_filepaths, batch_classes)
        else:
            batch_filepaths = np.array(self.filepath_array[self.index : self.index + self.batch_size])
            batch_images = np.array([np.asarray(Image.open(i).convert("RGB").resize(self.target_size))[..., :3] for i in batch_filepaths]).astype(np.float32)
            batch_images = preprocess_input(batch_images)
            batch_classes = self.class_array[self.index : self.index + self.batch_size]
            self.index += self.batch_size
            return (batch_images, batch_filepaths, batch_classes)



##########################
# ImageGeneratorV2 Class #
##########################
# ImageGeneratorV2 is for shell_v2 purpose
class ImageGeneratorV2():
    def __init__(self, filepath_array, batch_size, target_size):
        self.filepath_array = filepath_array
        self.batch_size = batch_size
        self.target_size = target_size
        self.steps = int(np.math.ceil(len(self.filepath_array) / self.batch_size))
        self.index = 0
    
    def __iter__(self):
        return self
    
    def __len__(self):
        return len(self.filepath_array)
    
    def __next__(self):
        if self.index == self.__len__():
            raise StopIteration
        elif self.index + self.batch_size >= self.__len__():
            batch_filepaths = np.array(self.filepath_array[self.index : self.__len__()])
            batch_images = np.array([np.asarray(Image.open(i).convert("RGB").resize((self.target_size, self.target_size)))[..., :3] for i in batch_filepaths]).astype(np.float32)
            batch_images = preprocess_input(batch_images)
            self.index = self.__len__()
            return (batch_images, batch_filepaths)
        else:
            batch_filepaths = np.array(self.filepath_array[self.index : self.index + self.batch_size])
            batch_images = np.array([np.asarray(Image.open(i).convert("RGB").resize((self.target_size, self.target_size)))[..., :3] for i in batch_filepaths]).astype(np.float32)
            batch_images = preprocess_input(batch_images)
            self.index += self.batch_size
            return (batch_images, batch_filepaths)


##########################
# Preprocessing Features #
##########################
def get_class_folders_from_main_directory(directory):
    sub_folders = next(os.walk(directory))[1]
    for i in range(len(sub_folders)):
        sub_folders[i] = directory + sub_folders[i]
    return sorted(sub_folders)

def extract_classes_sub_folder_and_create_targets(sub_folders):
    all_image_filepaths = []
    for class_folder in sub_folders:
        image_files = os.listdir(class_folder)
        image_filepaths = list(map(lambda x : os.path.join(class_folder, x), image_files))
        all_image_filepaths += image_filepaths
    return all_image_filepaths




######################
# Evaluation Helpers #
######################
def evaluate_one_class_mean(testFeat, testGt, trainFeat, trainGt, verbose=True, withNorm=True):
    if type(trainFeat) is list:
        featList = trainFeat.copy()
        numClass = len(featList)
    else:
        featList = []
        numClass = np.max(trainGt)+1
        for i in range(numClass):
            featList.append(trainFeat[trainGt==i])
    trainTime = 0
    testTime = 0
    scores = np.zeros([testFeat.shape[0], numClass])
    for i in range(numClass):
        sOCM = OneClassMean()
        # training
        start = timeit.default_timer()
        sOCM.fit(featList[i])
        stop = timeit.default_timer()
        trainTime = trainTime + stop-start
        # testing
        start = timeit.default_timer()
        scores[:,i] = sOCM.score(testFeat, withNorm=withNorm)
        stop = timeit.default_timer() 
        testTime = testTime + stop-start
    trainTime = trainTime/numClass
    testTime = testTime/numClass
    if verbose:
        print('Train Time: ', trainTime)
        print('Test Time: ', testTime)
    labelEst = np.argmax(scores, axis=1)
    meanEST, mapEST, rocEST = _evaluate(labelEst, scores, testGt, verbose)
    return meanEST, mapEST, rocEST


def _evaluate(predictions, scores, groundtruth, verbose=True):
    """Performs metrics calculation for generated shell for all classes.
    Args:
        predictions (np.ndarray): Model output prediction array
        scores (np.ndarray): Model output score array
        groundtruth (np.ndarray): Groundtruth array
        verbose (boolean): To output metrics to cli/cell

    Returns:
        precision (float): Precision metric
        mean_average_precision (float): Mean Average Precision metric
        roc (float): ROC score metric
    """
    num_class = np.max(groundtruth) + 1
    precision = np.mean(predictions == groundtruth)
    mean_average_precision = average_precision_score(predictions == groundtruth, np.max(scores, axis=1))
    topX = np.zeros(num_class)
    roc = np.zeros(num_class)
    for i in range(num_class):
        roc[i] = roc_auc_score(groundtruth == i, scores[:,i])
        ind = np.argsort(-scores[:,i])
        topX[i] = sum(groundtruth[ind[:1000]] == i)
    if verbose:
        print('Mean:', precision)
        print('MAP:', mean_average_precision)
        print('AUROC:', np.mean(roc))
        print('ROC:', roc)
        print('TopX:', topX)
    return precision, mean_average_precision, roc


#################
# Shell Helpers #
#################
def fit_to_list(feat, groundtruth):
    """Creates a list of array of features for each groundtruth class present in the dataset
    Args:
        feat (np.ndarray): Feature array for each class
        groundtruth (np.ndarray): Groundtruth class array

    Returns:
        feat_list (list): List of feature arrays where the index is the
            feature array of the class id
    """
    feat_list = []
    num_class = np.max(groundtruth) + 1
    for i in range(num_class):
        feat_list.append(feat[groundtruth == i])
    return feat_list


def normalize(data, mean=None):
    """Perform normalization of feature array.
    Args:
        data (np.ndarray): Raw feature array (unnormalized)
        mean (float): Mean for the class shell

    Returns:
        normalized_data (np.ndarray): Normalized feature array
        mean (float): Mean of the raw feature array 
    """
    raw_data = data.copy()
    if mean is None:
        mean = np.mean(raw_data, axis =0, keepdims=True)
    normalized_data = raw_data - mean
    normalized_data = normalized_data / np.linalg.norm(normalized_data, axis =1, keepdims=True)
    return normalized_data, mean


def sorted_neighbors_of_i(m_all, i):
    neighbors = np.zeros(m_all.shape[0])
    for j in range(m_all.shape[0]):
        neighbors[j] = np.linalg.norm(m_all[i,:]-m_all[j,:])
    return neighbors, np.argsort(neighbors)


def class_and_outliers(gt, trueClass, outlierPercentage, outlierClassList=[]):
    num_class = np.max(gt)+1
    if len(outlierClassList) == 0:
        for i in range(num_class):
            if not i == trueClass:
                outlierClassList.append(i)
    finalMask = np.zeros(gt.size, dtype=bool)
    outlierPerClass = int(np.sum(gt==trueClass)*outlierPercentage/len(outlierClassList))
    for c in outlierClassList:
        mask = gt == c
        ind = np.where(mask)[0]
        finalMask[sample(list(ind),outlierPerClass)] = 1
    finalMask[gt==trueClass] = 1
    return finalMask


def update_global_mean_and_shell_mean(self, data_generator, raw_mapping):
    """To be used for updating shells
    """
    # Extract features and prepare for shell creation
    for data in data_generator:
        images = data[0]
        filepaths = data[1]
        classes = data[2]
        unique_classes = np.unique(classes)
        for class_index in unique_classes:
            # Generate class features
            indexes = np.where(classes == class_index)
            target_images = images[indexes]
            # Update shell family params
            if self.global_mean is None:
                self.global_mean = np.mean(class_features,
                                            axis=0,
                                            keepdims=True)
            else:
                self.global_mean = np.mean(
                    np.concatenate(
                        [
                            np.repeat(
                                self.global_mean,
                                self.instances,
                                axis=0
                            ),
                            class_features
                        ]
                    ),
                    axis=0,
                    keepdims=True
                )
            self.instances += class_features.shape[0]
            class_name = raw_mapping[class_index]
            # Append raw features to classifiers
            if self.classifiers[class_name].raw_features is None:
                self.classifiers[class_name].raw_features = class_features
            else:
                self.classifiers[class_name].raw_features =\
                    np.concatenate([self.classifiers[class_name].raw_features,
                                    class_features])
    # Create shells from features
    self.update_shells(self.global_mean)


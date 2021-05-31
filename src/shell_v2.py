import pickle
import timeit
from collections import OrderedDict
import os
import sys
sys.path.append(os.path.dirname(__file__))

import numpy as np
from tqdm import tqdm
from sklearn.svm import OneClassSVM
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input as vgg16_preprocess_input
from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet50_preprocess_input
from tensorflow.keras.applications import MobileNet
from tensorflow.keras.applications.mobilenet import preprocess_input as mobilenet_preprocess_input
from tensorflow.keras.layers import GlobalAvgPool2D
from tensorflow.keras import Model, Sequential
from tensorflow.keras.preprocessing import image

from utils import normalize
from utils import sorted_neighbors_of_i
# from utils import evaluate
from utils import fit_to_list

ACCEPTED_PREPROCESSORS = ("vgg16", "resnet50", "mobilenet")
PREPROCESSORS_PREPROCESS_FUNCTIONS = {'vgg16': vgg16_preprocess_input,
                                      'resnet50': resnet50_preprocess_input,
                                      'mobilenet': mobilenet_preprocess_input}
# assumes data has been pre-normalized
class ShellModel:
    """Creates a shell for one class mean.
    """
    def __init__(self):
        self.shell_id = None
        self.raw_features = None
        self.shell_mean = None
        self.num_instances = None
        self.noise_mean = None
        self.noise_std = None
        self.created_at = None
        self.updated_at = None

    def fit(self, global_mean):
        """Generate the shell parameters based on the global mean the shell family currently sees
        """
        self.__generate_one_class_mean(global_mean)

    def __generate_one_class_mean(self, global_mean):
        """Generate the one class mean which is the 'center' of the shell along with its 'diameter'
        """
        normalized_features, _ = normalize(self.raw_features, global_mean)
        normalized_mean = np.mean(normalized_features, axis=0, keepdims=True)
        # normalized_mean = np.mean(self.raw_features, axis=0, keepdims=True)
        # noise = self.raw_features - normalized_mean
        noise = normalized_features - normalized_mean
        noise = np.linalg.norm(noise, axis=1)
        self.shell_mean = normalized_mean
        self.num_instances = normalized_features.shape[0]
        self.noise_mean = np.median(noise)
        self.noise_std = np.median(np.absolute(noise - np.mean(noise)))

    def score(self, feat, global_mean, with_norm=True):
        """Perform a distance score based on how far a feature is from the shell
        """
        # smaller scores are better, muliply - to reverse that
        score = self.__generate_one_class_mean_score(feat, global_mean, with_norm=with_norm)
        return -score

    def __generate_one_class_mean_score(self, feat, global_mean, with_norm=True):
        """Perform a distance score based on how far a feature is from the shell.
        """
        if with_norm:
            feat_, _ = normalize(feat, global_mean)
        else:
            feat_ = feat.copy()  
        feat_ = feat_ -  self.shell_mean
        feat_ = np.linalg.norm(feat_, axis=1)
        shell_score = (feat_ - self.noise_mean) / self.noise_std
        return shell_score

    def update(self, feat, global_mean):
        """Perform an update to shell parameter. To be used for 1 data point of feature to
            update the model.
        """
        self.raw_features = np.concatenate([self.raw_features,
                                            feat])
        normalized_features, _ = normalize(self.raw_features, global_mean)
        self.shell_mean= np.mean(normalized_features,
                                 axis=0,
                                 keepdims=True)
        self.num_instances = normalized_features.shape[0]
        noise = normalized_features - self.shell_mean
        noise = np.linalg.norm(noise , axis=1)
        self.noise_mean = np.median(noise)
        self.noise_std = np.median(np.absolute(noise - np.mean(noise)))


class ShellFamily():
    def __init__(self):
        self.classifiers = OrderedDict()
        self.feature_extractor_model = None
        self.preprocessor = None
        self.global_mean = None
        self.instances = 0
        self.mapping = []
        self.created_at = None
        self.updated_at = None

    def create_preprocessor(self, feature_extractor_model):
        if feature_extractor_model in ACCEPTED_PREPROCESSORS:
            model = Sequential()  
            if feature_extractor_model == 'vgg':
                vgg = VGG16(weights='imagenet', include_top=False)
                model.add(vgg)
            elif feature_extractor_model == 'resnet50':
                resnet = ResNet50(weights='imagenet', include_top=False)
                model.add(resnet)
                model.add(GlobalAvgPool2D())
            elif feature_extractor_model == 'mobilenet':
                mobilenet = MobileNet(weights='imagenet', include_top=False)
                model.add(mobilenet)
                model.add(GlobalAvgPool2D())
            self.preprocessor = model
            self.feature_extractor_model = feature_extractor_model
            self.preprocessor_preprocess_function = PREPROCESSORS_PREPROCESS_FUNCTIONS[self.feature_extractor_model]
        else:
            raise ValueError("Preprocessor model not found! Please enter the following models: {}".format(ACCEPTED_PREPROCESSORS))
                
    def load(self, shell_file):
        with open(shell_file, "rb") as saved_data:
            shell_family_configuration = pickle.load(saved_data)
        for class_name in shell_family_configuration['classifiers']:
            self.classifiers[class_name] = shell_family_configuration['classifiers'][class_name]
        self.feature_extractor_model = shell_family_configuration['feature_extractor_model']
        self.mapping = shell_family_configuration['mapping']
        self.global_mean = shell_family_configuration['global_mean']
        self.instances = shell_family_configuration['instances']
        self.shell_file = shell_file
        self.create_preprocessor(self.feature_extractor_model)


    def fit(self, data_generator, raw_mapping):
        """To be used when creating an entire new family of shells
        """
        # Generate empty shell if needed
        for class_index in range(len(raw_mapping)):
            if raw_mapping[class_index] not in self.classifiers:
                self.classifiers[raw_mapping[class_index]] = ShellModel()
                self.mapping.append(raw_mapping[class_index])
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
                class_features = self.preprocessor.predict(target_images)
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
        # self.save(output_datafile)
        # self.shell_file = output_datafile
    
    def update_shells(self, global_mean):
        for shell_name in self.classifiers:
            self.classifiers[shell_name].fit(global_mean)
    
    def score(self, feat, threshold, with_update=True, return_full_results=True):
        results = OrderedDict()
        best_class_name = None
        best_class_index = None
        best_result = -9999999
        for class_name, shell in self.classifiers.items():
            results[class_name] = shell.score(feat, self.global_mean)
            if results[class_name] > best_result:
                best_class_name = class_name
                best_result = results[class_name]
                best_class_index = self.mapping.index(class_name)
        if with_update:
            self.global_mean = (self.global_mean * self.instances + feat) / (self.instances + 1)
            self.instances += 1
            self.classifiers[best_class_name].update(feat, self.global_mean)
        if return_full_results:
            return best_class_index, best_class_name, best_result, results
        else:
            return best_class_index, best_class_name, best_result

    # def scoreV2(self, feat, threshold, with_norm=True, with_update=True, add_new_class=True):
    #     results = OrderedDict()
    #     best_class_name = None
    #     best_class_index = None
    #     best_result = -9999999
    #     for class_name, shell in self.classifiers.items():
    #         results[class_name] = shell.score(feat, self.global_mean)
    #         if results[class_name] > best_result:
    #             best_class_name = class_name
    #             best_result = results[class_name]
    #             best_class_index = self.mapping.index(class_name)
    #     if best_result >= threshold:
    #         if with_update:
    #             self.global_mean = (self.global_mean * self.instances + feat) / (self.instances + 1)
    #             self.instances += 1
    #             self.classifiers[best_class_name].update(feat, self.global_mean)
    #     else:
    #         if add_new_class:
    #             self.create_new_class(feat)
    #     return best_class_index, best_class_name, best_result

    def save(self, output_filename):
        save_data = {'classifiers': self.classifiers,
                     'feature_extractor_model': self.feature_extractor_model,
                     'mapping': self.mapping,
                     'global_mean': self.global_mean,
                     'instances': self.instances}
        with open(output_filename, "wb") as data_file:
            pickle.dump(save_data, data_file)


    # def create_new_class(self, feat, new_class_name):
    #     """To be used when a family of shell is already present
    #     """
    #     shell = ShellModel()
    #     shell.fit(feat)
    #     self.mapping.append(new_class_name)
    #     self.classifiers[new_class_name] = shell
    #     with open(self.mapping_file, "w") as data_file:
    #         for class_name in self.mapping:
    #             data_file.write("%s\n" % class_name)
    #     with open(self.shell_file, "wb") as data_file:
    #         pickle.dump(self.classifiers, data_file)

    def delete_class(self, class_to_delete):
        """To be used when a shell needs to be deleted
        """
        all_features_total_value = self.global_mean * self.instances
        class_to_delete_raw_features_sum = np.sum(self.classifiers[class_to_delete].raw_features, axis=0)
        class_to_delete_raw_features_sum = np.expand_dims(class_to_delete_raw_features_sum, 0)
        self.global_mean = (all_features_total_value - class_to_delete_raw_features_sum) / (self.instances - self.classifiers[class_to_delete].num_instances)
        self.instances -= self.classifiers[class_to_delete].num_instances
        del self.classifiers[class_to_delete]
        # Re update all shell configurations
        self.update_shells(self.global_mean)
        # Save new configuration
        self.save(self.shell_file)



def normIt(data, m=None):
    nData = data.copy()
    #nData = data/np.linalg.norm(data, axis =1, keepdims=True)
    if m is None:
        m = np.mean(nData, axis =0, keepdims=True)
    nData = nData - m
    nData = nData/np.linalg.norm(nData, axis =1, keepdims=True)
    
    return nData, m

# def ocMean(feat):
#     m_ = np.mean(feat, axis=0, keepdims=True)
#     d = feat - m_
#     d = np.linalg.norm(d, axis=1)
#     model ={'clusMean': m_, 
#             'numInstance': feat.shape[0], 
#             'noiseMean': np.median(d), 
#             'noiseStd':np.median(np.absolute(d-np.mean(d))), 
#             'mean_norm': 0}
#     return model


# def ocMeanScore(feat, model, withNorm=True):
#     if withNorm:
#         feat_, _ = normalize(feat, model['mean_norm'])
#     else:
#         feat_ = feat.copy()  
#     feat_ = feat_ -  model['clusMean']
#     feat_ = np.linalg.norm(feat_, axis=1)
#     ss = (feat_ - model['noiseMean'])/model['noiseStd']
#     return ss


def evalOneClassMean(testFeat, testGt, trainFeat, trainGt, verbose=True, withNorm=True):
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
    meanEST, mapEST, rocEST = evaluate(labelEst, scores, testGt, verbose)
    return meanEST, mapEST, rocEST


# class StackedOneClassMean(OneClassMean):
#     """Create stacked shell of one class mean.
#     """
#     def __init__(self):
#         self.classifers = []

#     def fit(self, feat, target, multiMeans):
#         self.classifers = self.__generate_stacked_one_class_mean(feat, target, multiMeans)

#     def __generate_stacked_one_class_mean(self, feat, target, m_all):
#         _, neighs = sorted_neighbors_of_i(m_all, target)
#         classifers = []
#         current_shell = []
#         for i in neighs:
#             current_shell.append(i)
#             if len(current_shell)> 1:
#                 m1 = np.mean(m_all[current_shell,:], axis =0, keepdims=True)
#                 tf = feat-m1
#                 tf = tf/np.linalg.norm(tf, axis =1, keepdims=True)
#                 model = super(StackedOneClassMean, self).__generate_one_class_mean(tf)
#                 model['mean_norm'] = m1
#                 classifers.append(model)
#         tf = feat/np.linalg.norm(feat, axis =1, keepdims=True)
#         model = super(StackedOneClassMean, self).__generate_one_class_mean(tf)
#         model['mean_norm'] = np.zeros([1, feat.shape[1]])
#         classifers.append(model)
#         return classifers

#     def score(self, testFeat, with_norm=True):        
#         scores = self.__generate_stacked_one_class_mean_score(testFeat, with_norm)
#         labels = np.argmin(scores, axis=1)
#         return labels, -scores

#     def __generate_stacked_one_class_mean_score(self, feat, with_norm=True):
#         score = np.zeros([feat.shape[0], len(self.classifers)])
#         for i in range(len(self.classifers)):
#             score[:,i] = super(StackedOneClassMean, self).__generate_one_class_mean_score(feat, self.classifers[i])
#         return score


# def stackedMean(train_feat, target, m_all):
#     _, neighs = sorted_neighbors_of_i(m_all, target)
#     classifers = []
#     current_shell = []
#     for i in neighs:
#         current_shell.append(i)
#         if len(current_shell)> 1:
#             m1 = np.mean(m_all[current_shell,:], axis =0, keepdims=True)
#             tf = train_feat-m1
#             tf = tf/np.linalg.norm(tf, axis =1, keepdims=True)
#             model = ocMean(tf)
#             model['mean_norm'] = m1
#             classifers.append(model)
#     tf = train_feat/np.linalg.norm(train_feat, axis =1, keepdims=True)
#     model = ocMean(tf)
#     model['mean_norm'] = np.zeros([1,train_feat.shape[1]])
#     classifers.append(model)
#     return classifers


# def stackedMeanScore(classifers, test_feat):
#     score = np.zeros([test_feat.shape[0], len(classifers)])
#     for i in range(len(classifers)):
#         score[:,i] = ocMeanScore(test_feat, classifers[i])
#     return score


# def evalStackedOneClassMean(testFeat, testGt, trainFeat, trainGt, verbose=True):
#     sOCM = StackedOneClassMean()
#     sOCM.train(trainFeat, trainGt)
#     labelEst, scores = sOCM.score(testFeat)
#     meanEST, mapEST, rocEST = evaluate(labelEst, scores, testGt, verbose)
#     return meanEST, mapEST, rocEST


# class StackedMultiClassMean(StackedOneClassMean):
#     """Create multi class stacked shell class mean.
#     """
#     def __init__(self):
#         self.classifers = []

#     def fit(self, feat, gt=-1):
#         if type(feat) is list:
#             featList = feat.copy()
#             numClass = len(featList)
#         else:
#             featList = fit_to_list(feat, gt)
#             numClass = len(featList)
#         allMeans = np.zeros([numClass, featList[0].shape[1]])
#         for i in range(numClass):
#             allMeans[i,:] = np.mean(feat[i], axis =0)
#         self.classifers = self.__generate_stacked_multi_class_mean(featList, allMeans)

#     def __generate_stacked_multi_class_mean(self, featList, allMeans):
#         numClass = len(allMeans)
#         allClassifiers = []
#         for i in range(numClass):
#             target = i
#             classifers = super(StackedMultiClassMean, self).__generate_stacked_one_class_mean(featList[target], target, allMeans)
#             allClassifiers.append(classifers)
#         return allClassifiers
#     # def trainSingleClass(self, feat, target, multiMeans):
#     #     classifier = stackedMean(feat, target, multiMeans)
#     #     return classifier

#     def score(self, testFeat):        
#         scores = self.__generate_stacked_multi_class_mean_score(testFeat, self.classifers)
#         labels = np.argmin(scores, axis=1)
#         return labels, -scores

#     def __generate_stacked_multi_class_mean_score(self, testFeat, allClassifiers):
#         numClass = len(allClassifiers)
#         scores = np.zeros([testFeat.shape[0], numClass])
#         for i in range(numClass):
#             stacked_one_class_shell = super(StackedMultiClassMean, self).__generate_stacked_one_class_mean_score(allClassifiers[i], testFeat)
#             stacked_one_class_shell = np.mean(stacked_one_class_shell, axis =1)
#             scores[:,i] = stacked_one_class_shell
#         return scores


# def multiStackedOneClassMean(trainFeat, allMeans):
#     numClass = len(allMeans)
#     allClassifiers = []
#     for i in range(numClass):
#         target = i
#         classifers = stackedMean(trainFeat[target], target, allMeans)
#         allClassifiers.append(classifers)
#     return allClassifiers


# def scoreMultiStackedOneClassMean(testFeat, allClassifiers):
#     numClass = len(allClassifiers)
#     scores = np.zeros([testFeat.shape[0], numClass])
#     for i in range(numClass):
#         s = stackedMeanScore(allClassifiers[i], testFeat)
#         s = np.mean(s, axis =1)
#         scores[:,i] = s
#     return scores
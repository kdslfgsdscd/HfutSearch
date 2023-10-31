# -*- coding: utf-8 -*-
# @Author :Xu Tianyuan
# @Modifier :
# @Software: PyCharm
# Document purpose: VGG特征提取
import numpy as np
from numpy import linalg
from keras.applications.vgg16 import VGG16
from keras.preprocessing import image
from keras.applications.vgg16 import preprocess_input
from CommonFile import VGG_PARAMS
from PIL import Image as pilImage


class VGGNet:
    def __init__(self, **kwargs):
        self.inputShape = kwargs['inputShape']
        self.weight = kwargs['weight']
        self.pooling = kwargs['pooling']
        self.includeTop = kwargs['includeTop']
        self.modelVGG = VGG16(weights=self.weight, input_shape=self.inputShape, pooling=self.pooling, include_top=False)

    def VGGExtractFeat(self, imgPath):
        img = image.load_img(imgPath)
        imgSize = img.size
        changeSize = (self.inputShape[0], self.inputShape[1])
        if imgSize != changeSize:
            img = img.resize(changeSize, pilImage.NEAREST)
        img = image.img_to_array(img)
        img = np.expand_dims(img, axis=0)
        img = preprocess_input(img)
        feat = self.modelVGG.predict(img)
        normFeat = feat[0] / linalg.norm(feat[0])
        return normFeat, imgSize

    @classmethod
    def CreateVGGNet(cls):
        return cls(**VGG_PARAMS)

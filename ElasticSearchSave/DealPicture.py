# -*- coding: utf-8 -*-
# @Author :Xu Tianyuan
# @Modifier :
# @Software: PyCharm
# Document purpose:保存图片特征以及有效信息到es，移动图片数据到静态资源文件夹。
import os
from VGGNet import VGGNet
import numpy as np
import h5py
from CommonFile import DEAL_PARAMS
import shutil
from pathlib import Path
import time
import uuid
from elasticsearch import helpers
from datetime import datetime
from elasticsearch_dsl.connections import connections

class PictureDeal:

    def __init__(self, logger, maxDicFile, **kwargs):
        self.picSearResPos = kwargs['picSearResPos']
        self.maxFileCount = kwargs['maxFileCount']
        self.picVGGDB = kwargs['picVGGDB']
        self.picSearTempPos = kwargs['picSearTempPos']
        params = kwargs['esConnect']
        self.es = connections.create_connection(**params)
        self.esIndex = kwargs['INDEX']
        self.esType = kwargs['TYPE']
        self.featureDS = kwargs['featureDS']
        self.imgPathDS = kwargs['imgPathDS']
        self.imgNameFront = kwargs['imgNameFront']
        self.picSavePos = kwargs['picSavePos']
        self.maxTargetDic = maxDicFile[0]
        self.remainFileCout = self.maxFileCount - maxDicFile[1]
        self.model = VGGNet.CreateVGGNet()
        self.picLog = logger
        self.picDict={}

    def CalculDeal(self, imgList):

        if self.remainFileCout <= 0:
            self.maxTargetDic += 1
            self.remainFileCout = self.maxFileCount
        targetDicPath = os.path.join(self.picSavePos, str(self.maxTargetDic))
        targetDic = Path(targetDicPath)
        h5FeatureDS = self.featureDS + str(self.maxTargetDic)
        h5ImgPathDS = self.imgPathDS + str(self.maxTargetDic)
        if not targetDic.is_dir():
            os.mkdir(targetDicPath)
        featList, desImgList,picSet = self.OutputFeature(imgList, targetDicPath,
                                                  os.path.join(self.imgNameFront, str(self.maxTargetDic)))
        addFileCount = self.SaveExtractInfo(featList, desImgList, h5FeatureDS, h5ImgPathDS)
        self.PictureSaveES()
        self.remainFileCout -= addFileCount
        return picSet
    def OutputFeature(self, imgList, targetDic, maxDic):
        picSet=set()
        featList = []
        desImgList = []
        for srcImgPath in imgList:
            try:
                normFeat, imgSize = self.model.VGGExtractFeat(srcImgPath)
                imgName = os.path.split(srcImgPath)[1]
                desImgPath = os.path.join(targetDic, imgName)
                strSize = str(imgSize[0]) + 'X' + str(imgSize[1])
                imgSavePath = os.path.join(maxDic, imgName)
                imgSavePath = imgSavePath + strSize
                shutil.move(srcImgPath, desImgPath)
                featList.append(normFeat)
                desImgList.append(imgSavePath)
                picSet.add(imgName)
                self.picDict[imgName]=imgSavePath
            except:
                self.picLog.error(srcImgPath + ':photo exception！')
        return featList, desImgList,picSet

    def OpenH5py(self):
        h5File = h5py.File(self.picVGGDB)
        while h5File.mode != 'r+':
            time.sleep(10)
            h5File.close()
            h5File = h5py.File(self.picVGGDB)
        return h5File

    def SaveExtractInfo(self, featList, desImgList, h5FeatureDS, h5ImgPathDS):
        feats = np.array(featList)
        shapeLen = list(feats.shape)
        h5File = self.OpenH5py()
        try:
            if not h5ImgPathDS in h5File and not h5FeatureDS in h5File:
                shapeLen[0] = None
                strDataSet=h5File.create_dataset(h5ImgPathDS, (len(desImgList),), maxshape=tuple([None, ]), dtype=h5py.string_dtype())
                strDataSet[:]=desImgList
                h5File.create_dataset(h5FeatureDS, data=feats, maxshape=tuple(shapeLen))
            else:
                datasetFeat = h5File[h5FeatureDS]
                datasetImg = h5File[h5ImgPathDS]
                oldLen = datasetImg.shape[0]
                newLen = oldLen + shapeLen[0]
                shapeLen[0] = newLen
                datasetFeat.resize(tuple(shapeLen))
                datasetImg.resize(tuple([newLen, ]))
                datasetFeat[oldLen:newLen] = feats
                datasetImg[oldLen:newLen] = desImgList
        except:
            self.picLog.error('h5File open error!')
        finally:
            h5File.close()
        return len(desImgList)

    def PictureSaveES(self):
        try:
            elemList = []
            for key, value in self.picDict.items():
                esId = str(uuid.uuid4())
                imgName = key
                imgPath = value
                saveDate = datetime.today()
                elem = {
                    "_index": self.esIndex,
                    "_type": self.esType,
                    "_id": esId,
                    "_source": {
                        "img_name": imgName,
                        "img_path": imgPath,
                        "save_date": saveDate
                    }
                }
                elemList.append(elem)
            helpers.bulk(self.es, elemList)
        except:
            self.picLog.error("saving to es error!")
        finally:
            self.picDict.clear()

    @classmethod
    def CreatePicDeal(cls, logger, maxDicFile):
        return cls(logger, maxDicFile, **DEAL_PARAMS)

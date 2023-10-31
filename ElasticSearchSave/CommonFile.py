# -*- coding: utf-8 -*-
# @Author :Xu Tianyuan
# @Modifier :
# @Software: PyCharm
# Document purpose:公用变量以及函数
import os
import hashlib
baseDir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
webPicDir = os.path.join(baseDir, 'HfutSearch/static')

VGG_PARAMS = {
    'weight': 'imagenet',
    'inputShape': (224, 224, 3),
    'includeTop': False,
    'pooling': 'max',
}

configIfno = {
    'settingFile': os.path.join(baseDir, "ProcessSetting"),
    'tempImg': os.path.join(baseDir, "Images") + '/*.jpg',
    'OPENED': 'OPENED',
    'CLOSED': 'CLOSED',
    'PIC_MAX_DEAL':500,
    'PIC_MIN_INSERT': 300,
    'TEXT_MIN_INSERT': 1000,
    'INIT_WAIT_MAX_TIME':30,
    'END_WAIT_MAX_TIME':120
}

SAVE_ES_PARAMS = {
    'INDEX': 'hfut_search',
    'TYPE': 'hfut_type',
    'WEIGHT': 10,
    'reItemName': 'HfutSpider:items',
    'esConnect':{
            "host": "localhost",
            "port": 16110
        }

}

DEAL_PARAMS = {
    'picSearTempPos': baseDir + '/Images/*.jpg',
    'picVGGDB': baseDir + '/VGGGFatureCNN.h5',
    'picSearResPos': webPicDir + '/Result/*',
    'picSavePos': webPicDir + '/Result',
    'featureDS': 'featureDS',
    'imgPathDS': 'imgPathDS',
    'imgNameFront': 'Result',
    'maxFileCount': 5000,

    'INDEX': 'hfut_pic',
    'TYPE': 'hfut_pic_type',
    'esConnect': {
        "host": "localhost",
        "port": 16110
    }

}

LOGGER_PARAMS = {
    'PIC_LOG': 'PIC_LOG',
    'ERROR_LOG': 'ERROR_LOG',
    'PIC_FILE':'./dataFile/picLog.log',
    'ERROR_FILE':'./dataFile/error.log'
}

def GetMd5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


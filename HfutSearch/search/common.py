# -*- coding: utf-8 -*-
# @Author :Xu Tianyuan
# @Modifier :
# @Software: PyCharm
# Document purpose: 设置公用变量以及公用函数
import urllib
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import h5py
import glob
import os
import uuid
import codecs
import json
import hashlib
import re
VGG_PARAMS = {
    'weight': 'imagenet',
    'inputShape': (224, 224, 3),
    'includeTop': False,
    'pooling': 'max',
}
#es连接设置
connStr={
        "host": "localhost",
        "port": 16110
    }
#每次读取图片变量起始、结束以及每次读取总个数变量设置，以及热门检索起始以及结束变量设置
FETCH_NUMBER_DEF = {
    'start': 0,
    'end': 29,
    'len': 30,
    'pageNum':10,
    'redisTopStart':0,
    'redisTopEnd':5
}

#设置上传图片存活时间
EXPIRE_TIME = 3600
#筛选图片
MIN_SCORE = 0.75
HTTP = 'http://'

#字符串dataset名称
DEAL_PARAMS = {
    'featureDS': 'featureDS',
    'imgPathDS': 'imgPathDS'
}

UPLOAD_TYPE = {
    "SUBMIT": "SUBMIT",
    "DRAG": "DRAG",
    "URL": "URL",
    "LINK": "LINK",#link是通过查询结果跳转的
    "NONE": "NONE"
}
#设置es查询约束
CONSTVALUE={
    'NULL_DATE':'0001-01-01',
    'SHOW_CHAR_NUM':100
}

#url中/?.字符替换成其他字符串防止不能作为文件名
URL_PARAM={
    'differeNum':-5,
    'BACKLASH':'+Z_*-',
    'QUEST':'*+Y_-',
    "URLDOT":"_XTA_"
}

def GetMd5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()

#获取上传图片路径，其中link是通过查询结果跳转的
def CreateImgNamePath(imgName, loadType):
    if loadType != UPLOAD_TYPE['LINK']:
        imgPath = settings.UPLOAD_DIR + imgName + '.jpg'
        return imgPath, imgName

    imgPath = os.path.join(settings.LINK_DIR, imgName)
    imgName = GetMd5(imgName)
    return imgPath, imgName


def DownloadImgData(imgInfo, loadType, imgName):
    imgPath, imgName = CreateImgNamePath(imgName, loadType)
    if loadType == UPLOAD_TYPE['URL']:
        urllib.request.urlretrieve(url=imgInfo, filename=imgPath)
    else:
        default_storage.save(imgPath, ContentFile(imgInfo.read()))
    return imgPath, imgName


def ReturnTopn(start, end, conn):
    topnSearch = conn.zrevrangebyscore("hotSearchSet", "+inf", "-inf", start=start, num=end)
    strList = [(bytes.decode(byItem),urllib.parse.quote(byItem)) for byItem in topnSearch]
    return strList


def FetchImgPath(imgName, start, end, conn):
    byteList = conn.zrangebyscore(imgName, start, end)
    strList = [bytes.decode(byItem) for byItem in byteList]
    return strList

#只保留图片的真实路径
def OnlyImgPath(imgStr):
    return os.path.splitext(imgStr)[0] + '.jpg'


def CreateImgName():
    return str(uuid.uuid4()).replace('-', '')

#获取最终图片路径以及其他信息
def ChangeResImg(resImgList, client):
    urlList = [HTTP + ChangeNameToUrl(item)[0] for item in resImgList]
    urlTitle = FetchTitle(client, urlList)
    targetList = []
    for item in resImgList:
        imgPath = OnlyImgPath(item)
        imgUrl, imgSize = ChangeNameToUrl(item)
        imgTitle = urlTitle[imgUrl] if imgUrl in urlTitle else ''
        targetList.append([imgPath, imgUrl, imgSize, imgTitle])
    return targetList

#用于筛选院系
def ReadJsonData():
    dic = {}
    with codecs.open(settings.JSON_DATA, 'r', encoding='utf-8') as f:
        dic = json.load(f)
    return dic

#把图片文件名称转为url
def ChangeNameToUrl(imgName):
    try:
        imgPath = os.path.split(imgName)[1]
        pathSplit = os.path.splitext(imgPath)
        imgSize= pathSplit[1][4:]
        imgUrl=pathSplit[0][:URL_PARAM['differeNum']].replace(URL_PARAM['BACKLASH'], '/')
        imgUrl=imgUrl.replace(URL_PARAM['QUEST'], '?')
    except:
        imgSize = ''
        imgUrl=''
    return imgUrl,imgSize


def GetDicH5py():
    try:
        targetDics = [int(dic[len(settings.SEARCH_DIR[:-1]):]) for dic in glob.glob(settings.SEARCH_DIR)]
        maxtargetDic = 0 if not len(targetDics) else max(targetDics) + 1
        h5File = h5py.File(settings.H5PY_FILE, 'r')
    except:
        maxtargetDic = 0
        h5File = None
    return maxtargetDic, h5File

#用于图片查询结果上的标题
def FetchTitle(client, urlList):
    try:
        response = client.search(
            index="hfut_search",
            body={
                "_source": ["url", "title"],
                "query": {
                    "terms": {
                        "url": urlList
                    }
                },
                "size": 30
            }
        )
        hitList = {}
        for hit in response["hits"]["hits"]:
            if "title" in hit["_source"] and "url" in hit["_source"]:
                hitList[hit["_source"]["url"][len(HTTP):]] = hit["_source"]["title"]
    except:
        hitList = {}

    return hitList

#确定有效字符个数
def GetStripLabelLen(str):
    return len(re.sub('</?span.*?>','',str))

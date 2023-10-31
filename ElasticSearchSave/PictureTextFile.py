# -*- coding: utf-8 -*-
# @Author :Xu Tianyuan
# @Modifier :
# @Software: PyCharm
# Document purpose: 主文件，用于文本和图片循环获取进行保存es以及图片特征保存，
# 采用最长等待时间以及读取ProcessSetting文件判断是否结束
from DealPicture import PictureDeal
from SaveEs import DealRedis
from CommonFile import configIfno, SAVE_ES_PARAMS,DEAL_PARAMS
from scrapy_redis import connection
from scrapy.utils.project import get_project_settings
import glob
import sys
import time
from AllLoggerFile import  AllLogger

def ReadFile(path,logger):
    try:
        with open(path, 'r') as f:
            statusSpider = f.read()
        return statusSpider.split(":")
    except:
        logger.error('read file error!')


def getKeyLen(server):
    return server.llen(SAVE_ES_PARAMS['reItemName'])


def getImgListLen():
    imgList = glob.glob(configIfno['tempImg'])
    return imgList, len(imgList)


if __name__ == "__main__":
    settings = get_project_settings()
    server = connection.from_settings(settings)
    logger=AllLogger.InitErrorLog()
    try:
        targetDics = [int(dic[len(DEAL_PARAMS['picSearResPos'][:-1]):]) for dic in glob.glob(DEAL_PARAMS['picSearResPos'])]
        maxTargetDic= max(targetDics) if len(targetDics) else 0
        maxDicFiles = glob.glob(DEAL_PARAMS['picSearResPos'][:-1] + str(maxTargetDic) + '/*')
        FileCount = len(maxDicFiles)
    except:
        maxTargetDic = 0
        FileCount=0
        logger.error('catalogue name is wrong！')
    picDeal = PictureDeal.CreatePicDeal(logger,(maxTargetDic,FileCount))
    esSave = DealRedis.CreateDealRedis(server,logger)
    statusSpider = ReadFile(configIfno['settingFile'],logger)
    count=0
    while not getKeyLen(server) and(not statusSpider or
                              len(statusSpider )!=2 or statusSpider[1] == configIfno['CLOSED']):
        time.sleep(10)
        count=count+1
        if count==configIfno['INIT_WAIT_MAX_TIME']:
            logger.error('spider error running!')
            sys.exit(0)
        statusSpider = ReadFile(configIfno['settingFile'],logger)
    count=0
    picSet=set()
    while True:
        imgList, imglen = getImgListLen()
        if imglen > configIfno['PIC_MIN_INSERT']:
            count=0
            imgList=list(set(imgList)-picSet)
            resPicSet=picDeal.CalculDeal(imgList[:configIfno['PIC_MAX_DEAL']])
            picSet=set.union(picSet,resPicSet)
        if getKeyLen(server) > configIfno['TEXT_MIN_INSERT']:
            count=0
            esSave.ReadRedis(configIfno['TEXT_MIN_INSERT'])
        imgList, imglen = getImgListLen()
        redisCount=getKeyLen(server)
        if imglen <= configIfno['PIC_MIN_INSERT'] and redisCount <= configIfno['TEXT_MIN_INSERT']:
            statusSpider = ReadFile(configIfno['settingFile'],logger)
            if  count==configIfno['END_WAIT_MAX_TIME'] or \
                    (statusSpider and len(statusSpider) == 2 and statusSpider[1] == configIfno['CLOSED']):
                esSave.ReadRemain()
                imgList, imglen = getImgListLen()
                imgList = list(set(imgList) - picSet)
                if len(imgList):
                    picDeal.CalculDeal(imgList)
                if count==configIfno['END_WAIT_MAX_TIME']:
                    logger.error('spider  error closing！')
                break
            time.sleep(30)
            if redisCount==getKeyLen(server):
                count = count + 1


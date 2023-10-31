# -*- coding: utf-8 -*-
# @Author :Xu Tianyuan
# @Modifier :
# @Software: PyCharm
# Document purpose: 记录日志
import  logging
from CommonFile import LOGGER_PARAMS

class AllLogger:
    @staticmethod
    def InitPicLog():
        logFile = logging.FileHandler(LOGGER_PARAMS['PIC_FILE'], 'w')
        dataLog = logging.Logger(LOGGER_PARAMS['PIC_LOG'], level=logging.INFO)
        dataLog.addHandler(logFile)
        return dataLog

    @staticmethod
    def InitErrorLog():
        logFile = logging.FileHandler(LOGGER_PARAMS['ERROR_FILE'], 'a')
        fat = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s")
        logFile.setFormatter(fat)
        dataLog = logging.Logger(LOGGER_PARAMS['ERROR_LOG'], level=logging.ERROR)
        dataLog.addHandler(logFile)
        return dataLog

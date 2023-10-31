# -*- coding: utf-8 -*-
# @Author :Xu Tianyuan
# @Modifier :
# @Software: PyCharm
# Document purpose:保存文本信息到es中
import json
from CommonFile import SAVE_ES_PARAMS, GetMd5
from elasticsearch import helpers
from scrapy_redis.utils import bytes_to_str
from datetime import datetime
from elasticsearch_dsl.connections import connections


class DealRedis(object):

    def __init__(self, server, logger, **kwargs):
        self.server = server
        self.bulkElems = []
        params = kwargs['esConnect']
        self.es = connections.create_connection(**params)
        self.esIndex = kwargs['INDEX']
        self.esType = kwargs['TYPE']
        self.esWeight = kwargs['WEIGHT']
        self.reItemName = kwargs['reItemName']
        self.esLog = logger

    def ReadRedis(self, lens):
        for i in range(lens):
            data = self.server.lpop(self.reItemName)
            if data:
                self.ReadData(data)
        if len(self.bulkElems):
            self.SaveBulk()

    def ReadData(self, data):
        data = bytes_to_str(data)
        data = json.loads(data)
        data = self.CreateEsType(data)
        self.bulkElems.append(data)
    #批量插入
    def SaveBulk(self):
        try:
            helpers.bulk(self.es, self.bulkElems)
        except:
            idList = [item['_id'] for item in self.bulkElems if '_id' in item]
            lines = json.dumps(idList, ensure_ascii=False)
            self.esLog.error(lines)
        finally:
            del self.bulkElems[:len(self.bulkElems)]
    #读取redis中剩余文本信息
    def ReadRemain(self):
        data = self.server.lpop(self.reItemName)
        while data:
            self.ReadData(data)
            data = self.server.lpop(self.reItemName)
        if len(self.bulkElems):
            self.SaveBulk()
    #获取搜索建议文本
    def GenSuggests(self, index, infoTuple):
        usedWords = set()
        suggests = []
        try:
            for text, weight in infoTuple:
                if text:
                    words = self.es.indices.analyze(index=index,
                                                    body={"analyzer": "ik_max_word", 'filter': ["lowercase"],
                                                          'text': text})
                    anylyzedWords = set([r["token"] for r in words["tokens"] if len(r["token"]) > 1])
                    newWords = anylyzedWords - usedWords
                else:
                    newWords = set()

                if newWords:
                    usedWords = set.union(usedWords, newWords)
                    suggests.append({"input": list(newWords), "weight": weight})
        except:
            self.esLog.error("create suggestion errror!")
        return suggests

    def CreateEsType(self, jsonData):
        url = jsonData['url']
        esId = GetMd5(url)
        title = jsonData['title'] if 'title' in jsonData else ""
        urlOrigin = jsonData['urlOrigin'] if 'urlOrigin' in jsonData else ""
        isIndex=jsonData['isIndex'] if 'isIndex' in jsonData else False
        content = jsonData['content'] if 'content' in jsonData else ""
        imageResult = jsonData['imageResult'] if 'imageResult' in jsonData else ""
        createStr="0001-1-1"
        if 'createdDate' in jsonData:
            createStr=jsonData['createdDate']
        try:
            createdDate = datetime.strptime(createStr, '%Y-%m-%d')
        except:
            createdDate=datetime.strptime("0001-1-1", '%Y-%m-%d')
        saveDate = datetime.today()
        elem = {
            "_index": self.esIndex,
            "_type": self.esType,
            "_id": esId,
            "_source": {
                "url": url,
                "title": title,
                "url_origin": urlOrigin,
                "content": content,
                "img_download":imageResult,
                "is_index":isIndex,
                "create_date": createdDate,
                "save_date": saveDate,
                "suggest": self.GenSuggests(self.esIndex, ((title, self.esWeight),))
            }
        }
        return elem

    @classmethod
    def CreateDealRedis(cls, server, logger):
        return cls(server, logger, **SAVE_ES_PARAMS)

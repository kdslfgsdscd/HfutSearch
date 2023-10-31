# -*- coding: utf-8 -*-
# @Author :Xu Tianyuan
# @Modifier :
# @Software: PyCharm
# Document purpose:  web后台服务，访问es以及redis等实现前后端交互
import json
from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse
from datetime import datetime
from django_redis import get_redis_connection
from search.VGGNet import VGGNet
import numpy as np
from PIL import Image
from search import common
from elasticsearch_dsl.search import Search
from elasticsearch_dsl.connections import connections

model = VGGNet.CreateVGGNet()
conn = get_redis_connection("default")

client = connections.create_connection(**common.connStr)
jsonData = common.ReadJsonData()

class IndexView(View):
    def get(self, request):
        topnSearch = common.ReturnTopn(common.FETCH_NUMBER_DEF['redisTopStart'],
                                       common.FETCH_NUMBER_DEF['redisTopEnd'], conn)
        return render(request, "index.html", {"topnSearch": topnSearch})

#此处这么设计的目的是相对于加了一个中间件让不同方式的上传方式最后都以一个同样的方式去处理即通过url方式
# ，这样在图片访问中自需要使用一个get方法即可
class UploadPictureMiddle(View):
    def post(self, request, uploadType):
        imgInfo = request.FILES.get('file')
        imgPath, imgName = common.DownloadImgData(imgInfo, uploadType, common.CreateImgName())
        return HttpResponse('{"imgName":"' + imgName + '","uploadType":"' + uploadType + '"}',
                            content_type='application/json')

#用于检索图片后的滚动浏览操作
class AjaxPictureMiddle(View):
    def ChangeInfoToHtml(self, resImgList, pageIndex):
        jsonObject = '{"pageIndex":"' + pageIndex + '","imgList":' + json.dumps(resImgList) + '}'
        return jsonObject

    def get(self, request):
        imgToken = request.GET.get('imgToken')
        start = request.GET.get('start')
        end = request.GET.get('end')
        imglist = common.FetchImgPath(imgToken, start, end, conn)
        resImgList = common.ChangeResImg(imglist, client)
        try:
            pageIndex = int(int(start) / common.FETCH_NUMBER_DEF['len'] + 1)
        except:
            pageIndex = 0
        htmlCode = self.ChangeInfoToHtml(resImgList, str(pageIndex))
        return HttpResponse(htmlCode, content_type='application/json')

#以图搜图
class SearchPictureView(View):

    def CreateZADD(self, imgName, sortTotalDict):
        for index, item in enumerate(sortTotalDict):
            conn.zadd(imgName, mapping={item[0]: index})
        conn.expire(imgName, common.EXPIRE_TIME)

    def FetchUserInfo(self, predictImgUrl, imgPath, imgName, start, end, total, querySize):
        userUpload = {}
        try:
            userUpload["imgUrl"] = imgPath.split('static/')[1]
        except:
            userUpload["imgUrl"] = imgPath
        userUpload["infoGuess"] = predictImgUrl
        userUpload["imgName"] = imgName
        urlDic = common.FetchTitle(client, [common.HTTP + predictImgUrl])
        userUpload["title"] = ''
        if predictImgUrl in urlDic:
            userUpload["title"] = urlDic[predictImgUrl]
        userUpload["height"] = querySize[1]
        userUpload["width"] = querySize[0]
        userUpload['start'] = start
        userUpload['end'] = end
        userUpload['total'] = total
        return userUpload

    def ReturnImgsPath(self, imgPath):
        sortTotalDict = {}
        querySize = (0, 0)
        maxtargetDic, h5File = common.GetDicH5py()
        if h5File:
            try:
                totalDict = {}
                queryVec, querySize = model.VGGExtractFeat(imgPath)
                for item in range(maxtargetDic):
                    featStr = common.DEAL_PARAMS['featureDS'] + str(item)
                    imgStr = common.DEAL_PARAMS['imgPathDS'] + str(item)
                    if featStr in h5File and imgStr in h5File:
                        feats = h5File[featStr][:]
                        imgPaths = h5File[imgStr][:]
                        scores = np.dot(queryVec, feats.T)
                        validData = np.where(scores > common.MIN_SCORE)[0]
                        for item in validData:
                            totalDict[imgPaths[item]] = scores[item]
                sortTotalDict = sorted(totalDict.items(), key=lambda x: x[1], reverse=True)
                h5File.close()
            except:
                h5File.close()
        return sortTotalDict, querySize

    def get(self, request, uploadType):
        imgInfo = request.GET['query']
        querySize = (0, 0)
        imgPath, imgName = common.CreateImgNamePath(imgInfo, uploadType) \
            if uploadType == common.UPLOAD_TYPE['DRAG'] or uploadType == common.UPLOAD_TYPE['LINK'] or uploadType == \
               common.UPLOAD_TYPE['SUBMIT'] \
            else common.DownloadImgData(imgInfo, uploadType, common.CreateImgName())
        if not conn.exists(imgName):
            sortTotalDict, querySize = self.ReturnImgsPath(imgPath)
            totalNum = len(sortTotalDict)
            self.CreateZADD(imgName, sortTotalDict)
        else:
            totalNum = conn.zcard(imgName)
            fp = Image.open(imgPath)
            if fp:
                querySize = fp.size
        resImgList = common.FetchImgPath(imgName, common.FETCH_NUMBER_DEF['start'],
                                         common.FETCH_NUMBER_DEF['end'], conn)
        upLoadInfo = self.FetchUserInfo(common.ChangeNameToUrl(resImgList[0])[0] if len(resImgList) else '', imgPath,
                                        imgName, common.FETCH_NUMBER_DEF['start'],
                                        common.FETCH_NUMBER_DEF['end'], totalNum, querySize)

        resImgList = common.ChangeResImg(resImgList, client)
        return render(request, "pictureResult.html", {"userUpload": upLoadInfo, "filesInfo": resImgList})

#搜索建议
class SearchSuggest(View):
    def get(self, request):
        keyWords = request.GET.get('s', '')
        kw = {'using': client,
              'index': 'hfut_search',
              'doc_type': 'hfut_type'
              }
        sugg = Search(**kw)
        sugg = sugg.suggest('my_suggest', keyWords, completion={
            "field": "suggest",
            "size": common.FETCH_NUMBER_DEF['pageNum']
        })
        sugg = sugg.execute()
        options = sugg.suggest['my_suggest'][0].options
        reDatas = [match._source["title"] for match in options]
        return HttpResponse(json.dumps(reDatas), content_type="application/json")
#院系筛选
class AjaxCollegeMiddle(View):
    def get(self, request):
        return HttpResponse(json.dumps(jsonData), content_type='application/json')

#文本检索以及热门检索
class SearchView(View):
    def get(self, request):
        keyWords = request.GET.get("q", "")
        page = request.GET.get("p", "1")
        urlType=request.GET.get("t","")
        collType=urlType.replace(common.URL_PARAM["URLDOT"],".")
        conn.zincrby("hotSearchSet", 1, keyWords)
        topnSearch = common.ReturnTopn(common.FETCH_NUMBER_DEF['redisTopStart'],
                                       common.FETCH_NUMBER_DEF['redisTopEnd'], conn)
        try:
            page = int(page)
        except:
            page = 1
        if page>50:
            page=50
        startTime = datetime.now()
        originBody={
                "query": {
                    "function_score": {
                        "query": {
                            "bool":{
                                "must":[
                                    {
                                        "bool": {
                                            "should": [
                                                {
                                                    "multi_match": {
                                                        "analyzer": "ik_smart",
                                                        "query": keyWords,
                                                        "fields": "title",
                                                        "boost": 2
                                                    }
                                                },
                                                {
                                                    "multi_match": {
                                                        "analyzer": "ik_smart",
                                                        "query": keyWords,
                                                        "fields": "content"
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        },
                        "script_score": {
                            "script": {
                                "lang": "painless",
                                "source": "int spanTime=params.keyword-doc.create_date.value.year;"
                                          "if(spanTime>0 && spanTime<params.keyword-1)return 1/spanTime;if( doc.is_index.value)return 1/1.1;return 1;",
                                "params": {
                                    "keyword": datetime.today().year
                                }
                            }
                        },
                        "boost_mode": "multiply"
                    }
                },
                "from": (page - 1) * common.FETCH_NUMBER_DEF['pageNum'],
                "size": common.FETCH_NUMBER_DEF['pageNum'],
                "highlight": {
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "title": {},
                        "content": {},
                    }
                }
            }

        if collType:
            originBody["query"]["function_score"]["query"]["bool"]["must"].append({"term": {
                    "url_origin": {
                      "value": collType
                    }
                  }})
        response = client.search(
            index="hfut_search",
            body=originBody
        )

        endTime = datetime.now()
        lastSeconds = (endTime - startTime).total_seconds()
        totalNums = response["hits"]["total"]
        pageNums = int(totalNums / common.FETCH_NUMBER_DEF['pageNum'])
        if totalNums % common.FETCH_NUMBER_DEF['pageNum']:
            pageNums += 1
        hitList = []
        for hit in response["hits"]["hits"]:
            hitDict = {}
            if "title" in hit["highlight"]:
                hitDict["title"] = "".join(hit["highlight"]["title"])
            else:
                hitDict["title"] = hit["_source"]["title"]
            if "content" in hit["highlight"]:
                hitDict["content"] = ""
                for item in hit["highlight"]["content"]:
                    hitDict["content"] += item
                    if common.GetStripLabelLen(hitDict["content"]) > common.CONSTVALUE['SHOW_CHAR_NUM']:
                        hitDict["content"] += "..."
                        break
            else:
                hitDict["content"] = hit["_source"]["content"][:common.CONSTVALUE['SHOW_CHAR_NUM']]
                if len(hit["_source"]["content"]) > common.CONSTVALUE['SHOW_CHAR_NUM']:
                    hitDict["content"] += '...'
            hitDict["url"] = hit["_source"]["url"]
            dates = hit["_source"]["create_date"].split('T')
            hitDict["createDate"] = dates[0] if len(dates) == 2 and dates[0] != common.CONSTVALUE['NULL_DATE'] and not hit["_source"]["is_index"] else ''
            hitDict["urlOrigin"] = jsonData[hit["_source"]["url_origin"]] \
                if hit["_source"]["url_origin"] in jsonData else hit["_source"]["url_origin"]
            hitList.append(hitDict)
        return render(request, "result.html", {"page": page,
                                               "hitList": hitList,
                                               "keyWords": keyWords,
                                               "totalNums": totalNums,
                                               "pageNums": pageNums,
                                               'topnSearch': topnSearch,
                                               "lastSeconds": lastSeconds
                                                ,"collList":json.dumps(jsonData)
                                               ,"collType":urlType})
#如果查询的图片信息未保存到redis中就新建，如果保存直接访问reids
class TxtPicSearch(View):
    def CreateZADD(self, keyWords, imgPathList):
        for index, item in enumerate(imgPathList):
            conn.zadd(keyWords, mapping={item: index})
        conn.expire(keyWords, common.EXPIRE_TIME)

    def get(self, request):
        keyWords = request.GET.get("q", "")
        redisKeys = common.GetMd5(keyWords)
        if not conn.exists(redisKeys):
            response = client.search(
                index="hfut_search",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "multi_match": {
                                        "analyzer": "ik_smart",
                                        "query": keyWords,
                                        "fields": "title"
                                    }
                                }
                            ],
                            "must_not": [
                                {
                                    "term": {
                                        "img_download": {
                                            "value": ""
                                        }
                                    }
                                }
                            ],
                            "filter": [
                                {"term": {"is_index": "false"}}
                            ]
                        }
                    },
                    "_source": "img_download",
                    "from": 0,
                    "size": 100
                }
            )
            imgNameList = ",".join([item['_source']['img_download'] for item in response["hits"]["hits"]]).split(",")
            response = client.search(
                index="hfut_pic",
                body={
                    "query": {
                        "terms": {
                            "img_name": imgNameList
                        }
                    },
                    "from": 0,
                    "size": len(imgNameList)
                }
            )
            imgNameList = [item['_source']['img_path'] for item in response["hits"]["hits"]]
            totalNum = len(imgNameList)
            self.CreateZADD(redisKeys, imgNameList)
        else:
            totalNum = conn.zcard(redisKeys)
        resImgList = common.FetchImgPath(redisKeys, common.FETCH_NUMBER_DEF['start'],
                                         common.FETCH_NUMBER_DEF['end'], conn)
        resImgList = common.ChangeResImg(resImgList, client)
        pageInfo = {
            'start': common.FETCH_NUMBER_DEF['start'],
            'end': common.FETCH_NUMBER_DEF['end'],
            'total': totalNum,
            "keysToken": redisKeys
        }
        return render(request, "textPicture.html",
                      {"pageInfo": pageInfo,
                       "filesInfo": resImgList,
                       "keyWords": keyWords})
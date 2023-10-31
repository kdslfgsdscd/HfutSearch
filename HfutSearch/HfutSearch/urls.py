# -*- coding: utf-8 -*-
# @Author :Template
# @Modifier :Xu Tianyuan
# @Software: PyCharm
# Document purpose: 创建url分发器
"""HfutSearch URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from search.views import SearchSuggest, SearchView, IndexView, SearchPictureView, \
    UploadPictureMiddle, AjaxPictureMiddle,TxtPicSearch,AjaxCollegeMiddle
from django.views.static import serve
from HfutSearch.settings import STATIC_ROOT
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),

    url(r'^searchPicture/(?P<uploadType>.*)/$', SearchPictureView.as_view(), name="searchPicture"),

    url(r'^uploadPicture/(?P<uploadType>.*)/$', UploadPictureMiddle.as_view(), name="uploadPicture"),

    url(r'^txtPicSearch/$', TxtPicSearch.as_view(), name="txtPicSearch"),

    url(r'^ajaxQuest/$', AjaxPictureMiddle.as_view(), name="ajaxQuest"),

    url(r'^ajaxCollege/$', AjaxCollegeMiddle.as_view(), name="ajaxCollege"),

    url(r'^suggest/$', SearchSuggest.as_view(), name="suggest"),

    url(r'^static/(?P<path>.*)$',serve,{'document_root':STATIC_ROOT}),

    url(r'^search/$', SearchView.as_view(), name="search"),
]

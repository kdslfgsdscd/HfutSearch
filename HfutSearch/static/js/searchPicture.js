/*
*  @Author :Xu Tianyuan
*  @Modifier :
*  @Software: PyCharm
*  Document purpose: 图片检索页面的一些js操作
* */
var picSearchVar = {
    camera: $("#camera"),
    searchInput: $(".searchInput"),
    //share
    inputText: $("#input_text"),
    searchButton: $('.searchButton'),
    allPos: $("html"),
    stBoxChildElem: $("#stBox *"),
    stBoxColse: $(".stBox-close"),
    stBox: $("#stBox"),
    stBoxChild: $("#stBoxChild"),
    uploadTip: $(".st_box .high-quality-load"),
    picHide: $("#pic_hide")//result
};
var PAGE_TYPE = {
    INDEX: "index",
    RESULT: "result"
};
var UPLOAD_TYPE = {
    SUBMIT: "SUBMIT",
    DRAG: "DRAG",
    URL: "URL",
    LINK: "LINK",//搜索结果页点击显示的图片搜索图标对应的方式
    NONE: "NONE"
};
var dragTimer = null;


$(document).keydown(function (event) {
    event.keyCode == 13 && picSearchVar.searchButton.click();
})

function Check() {
    var filePath = picSearchVar.inputText.val();
    filePath = filePath.replace(/(^\s*)|(\s*$)/g, '');
    if (filePath === 0)
        return false;
    if (filePath.length < 7 || (filePath.substring(0, 7) != 'http://' && filePath.substring(0, 8) != 'https://')) {
        alert("请输入以http://开头的网络图片地址！");
        return false;
    }
    var filePath = filePath.substring(8);
    if (filePath.indexOf('/') < 0) {
        alert("请输入正确的网络图片地址！");
        return false;
    }
    filePath = filePath.substring(filePath.lastIndexOf('.') + 1, filePath.length);
    filePath = filePath.toLowerCase();
    if (filePath.length < 5 && filePath != 'jpg' && filePath != 'png' && filePath != 'jpeg') {
        alert("抱歉，目前不支持此文件格式，请确认图片是JPG、PNG、JPEG格式。");
        return false;
    }
    return true;
}

function CheckUploadFile(target) {

    try {
        var fileSize = 0;
        var fileType = "";
        fileSize = target.files[0].size;
        fileType = target.files[0].type;

        if (fileSize > 5 * 1000 * 1000) {
            alert("您上传的文件过大，请选择小于5M的文件上传。");
            return false;
        }
        if (fileType.indexOf('image') < 0) {
            alert("抱歉，目前不支持此文件格式，请确认图片是JPG、PNG、JPEG格式。");
            return false;
        }
    } catch (e) {
    }
    return true;

}

function UploadFileChange(target, pageType) {

    if (CheckUploadFile(target)) {
        if (target.files.length) {
            UploadBackgroud(pageType);
            UploadImage(target.files[0], UPLOAD_TYPE.SUBMIT);
        }
    }
}

function UploadImage(file, uploadType) {
    var fd = new FormData();
    fd.append('file', file);
    var csrfToken = $("[name='csrfmiddlewaretoken']").val();
    $.ajax({
        url: "/uploadPicture/" + uploadType + '/',
        type: "POST",
        data: fd,
        processData: false,
        contentType: false,
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
        success: function (imgInfo) {
            location.href = "/searchPicture/" + imgInfo.uploadType + "/?" + "query=" + imgInfo.imgName;
        }
    });
};


function DragWindow(isShow, showTime, pageType) {

    pageType == PAGE_TYPE.INDEX && (isShow ? (picSearchVar.camera.hide(),
        picSearchVar.searchInput.attr('placeholder', '在此处粘贴图片网址')) : (picSearchVar.camera.show(),
        picSearchVar.searchInput.attr('placeholder', '进行文本搜索')));
    isShow ? picSearchVar.stBox.show(showTime) : picSearchVar.stBox.hide(showTime);
}

function DragClass(isShow) {
    picSearchVar.stBoxChild.removeClass(isShow ? "color_less" : "color_more");
    picSearchVar.stBoxChild.addClass(isShow ? "color_more" : "color_less");
}

function ClearTimer() {
    dragTimer && (clearTimeout(this.dragTimer), dragTimer = null);
}

function UploadBackgroud(pageType) {
    pageType == PAGE_TYPE.RESULT && picSearchVar.stBox.show();
    picSearchVar.picHide.hide();
    picSearchVar.uploadTip.show();
}

function DragStrategy() {
    try {

        var isDrag = false;
        if (typeof DragStrategy._initialized == "undefined") {

            $.extend(DragStrategy.prototype, {
                BindContainEvent: function (pageType) {

                    picSearchVar.stBoxChild.bind("dragover", function (event) {

                        pageType == PAGE_TYPE.INDEX && DragClass(true);

                    }).bind("dragleave", function (event) {

                        pageType == PAGE_TYPE.INDEX && DragClass(false);

                    }).bind("drop", function (event) {
                        event.stopPropagation();
                        event.preventDefault();
                        var dtf = event.originalEvent.dataTransfer;
                        if (!CheckUploadFile(dtf)) {
                            picSearchVar.stBoxChild.addClass("color_less");
                            pageType == PAGE_TYPE.RESULT && DragWindow(false, 0, pageType);
                            return false;
                        }
                        isDrag = true;
                        var files = dtf.files;
                        if (files.length > 0) {
                            UploadImage(files[0], UPLOAD_TYPE.DRAG);
                            UploadBackgroud(pageType);
                        }
                        isDrag = false;
                    });
                },


                BindPicHtmlEvent: function (pageType) {
                    $(picSearchVar.allPos).bind("dragover", function (event) {

                        pageType == PAGE_TYPE.RESULT && ClearTimer(),
                            DragWindow(true, 0, pageType), event.preventDefault();

                    }).bind('dragenter', function (event) {

                        pageType == PAGE_TYPE.RESULT &&
                        (ClearTimer(), DragWindow(true, 0, pageType)), event.preventDefault();

                    }).bind("dragleave", function (event) {

                        pageType == PAGE_TYPE.RESULT && (dragTimer = setTimeout(function () {
                            DragWindow(false, 0, pageType);
                            this.dragTimer = null;
                        }, 100)), event.preventDefault();

                    }).bind("drop", function (event) {

                        !isDrag && pageType == PAGE_TYPE.RESULT &&
                        DragWindow(false, 0, pageType), event.preventDefault();

                    });
                },

                BindEvent: function (pageType) {
                    picSearchVar.allPos.click(function (event) {
                        var target = $(event.target);
                        (target.is(picSearchVar.camera) && !picSearchVar.stBox.is(':visible') &&
                            (DragWindow(true, 500, pageType), true)) ||
                        ((picSearchVar.stBox.is(':visible') && ((!target.is(picSearchVar.stBoxChildElem) &&
                            !target.is(picSearchVar.stBox) && !target.is(picSearchVar.searchInput) && !target.is(picSearchVar.searchButton))
                            || target.is(picSearchVar.stBoxColse))) &&
                            DragWindow(false, 500, pageType))
                    });
                },
                init: function (pageType) {
                    pageType == PAGE_TYPE.INDEX && this.BindEvent(pageType);
                    this.BindPicHtmlEvent(pageType);
                    this.BindContainEvent(pageType);
                }
            });
            DragStrategy._initialized = true;
        }
    } catch (e) {

    }
}

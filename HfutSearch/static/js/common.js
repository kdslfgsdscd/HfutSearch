/*
*  @Author :Template
*  @Modifier :Xu Tianyuan
*  @Software: PyCharm
*  Document purpose: 前端一些js交互
* */
//搜索建议框
function SuggestWindow(searchText) {
    var tmpHtml = ""
    $.ajax({
        cache: false,
        type: 'get',
        dataType: 'json',
        url: '/suggest/' + "?s=" + encodeURIComponent(searchText),
        async: true,
        success: function (data) {
            for (var i = 0; i < data.length; i++) {
                tmpHtml += '<li><a href="' + searchUrl + '?q=' + encodeURIComponent(data[i] )+ '">' + data[i] + '</a></li>'
            }
            $(".dataList").html("")
            $(".dataList").append(tmpHtml);
            if (data.length == 0) {
                $('.dataList').hide()
            } else {
                $('.dataList').show()
            }
        }
    });

}

function hideElement(currentElement, targetElement) {
	if (!$.isArray(targetElement)) {
		targetElement = [ targetElement ];
	}
	$(document).on("click.hideElement", function(e) {
		var len = 0, $target = $(e.target);
		for (var i = 0, length = targetElement.length; i < length; i++) {
			$.each(targetElement[i], function(j, n) {
				if ($target.is($(n)) || $.contains($(n)[0], $target[0])) {
					len++;
				}
			});
		}
		if ($.contains(currentElement[0], $target[0])) {
			len = 1;
		}
		if (len == 0) {
			currentElement.hide();
		}
	});
};
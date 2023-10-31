/*
*  @Author :Template
*  @Modifier :
*  @Software: PyCharm
*  Document purpose:
* */
// 去除虚线框（会影响效率）
$(function () {
     $("a,input:checkbox,input:radio,button,input:button").live('focus', function () {
        $(this).blur();
    });
});



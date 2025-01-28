# 此为用于下载中小学官网教材的程序
url = input()
# https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=07f7d663-a867-4eb6-ad39-03b55dbd4a65&catalogType=tchMaterial&subCatalog=tchMaterial
new_code = ""
i = 83
while url[i] != '&':
    new_code += url[i]
    i += 1
print("https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/"+new_code+".pkg/pdf.pdf")
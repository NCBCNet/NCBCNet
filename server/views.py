from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
# Create your views here.
def index(request):
    return render(request,"server/index.html")


# easter egg 彩蛋部分

def easter_egg_1(request):
    return render(request,'server/easter_egg_1.html')

def about(request):
        return render(request,'server/about.html')

def illegal_request(request):
    return render(request,'server/illegal_request.html')

@api_view(['GET'])
def index_data(request):
    data = {
        "title": 'NCNet 南城网首页',
        "welcome_msg": "欢迎来到 NCBCNet 门户首页",
        "status": "success"
    }
    return Response(data)
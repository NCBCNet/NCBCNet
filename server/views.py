from django.shortcuts import render
# Create your views here.
def index(request):
    return render(request,"server/index.html")


# easter egg 彩蛋部分

def easter_egg_1(request):
    return render(request,'server/easter_egg_1.html')

def about(request):
        return render(request,'server/about.html')
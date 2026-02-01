from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View
from .models import UploadedFile
from .forms import UploadedFileForm
from django.shortcuts import redirect

# Create your views here.
@login_required(login_url='usermanage:login')
def FileList(request):
    if request.method == 'POST':
        form = UploadedFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('file_save:file_list')
        else:
            return HttpResponse(form.errors, status=400)
    else:
        form = UploadedFileForm()
        files = UploadedFile.objects.all()
        context = {'files': files, 'form': form}
        return render(request, 'file_save/file_list.html', context)

@login_required(login_url='usermanage:login')
def FileDelete(request, id):
    if request.method == 'POST':
        try:
            file_instance = UploadedFile.objects.get(id=id)
            file_instance.file.delete()  # 删除文件
            file_instance.delete()  # 删除数据库记录
            return redirect('file_save:file_list')
        except UploadedFile.DoesNotExist:
            return HttpResponse("文件未找到", status=404)
    else:
        return redirect('server:illegal_request')
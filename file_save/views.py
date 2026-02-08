from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from .models import UploadedFile, Folder
from .forms import UploadedFileForm, FolderForm
from django.shortcuts import redirect
from django.db.models import Q
import os
from django.conf import settings

# Create your views here.
@login_required(login_url='usermanage:login')
def FileList(request):
    folder_id = request.GET.get('folder')
    current_folder = None
    
    if folder_id:
        current_folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
    
    # 获取当前文件夹下的子文件夹
    if current_folder:
        folders = Folder.objects.filter(parent=current_folder, owner=request.user)
    else:
        folders = Folder.objects.filter(parent=None, owner=request.user)
    
    # 获取当前文件夹下的文件
    if current_folder:
        files = UploadedFile.objects.filter(folder=current_folder, owner=request.user)
    else:
        files = UploadedFile.objects.filter(folder=None, owner=request.user)
    
    # 获取面包屑导航
    breadcrumbs = []
    if current_folder:
        temp_folder = current_folder
        while temp_folder:
            breadcrumbs.insert(0, temp_folder)
            temp_folder = temp_folder.parent
    
    file_form = UploadedFileForm(user=request.user)
    folder_form = FolderForm()
    
    context = {
        'files': files,
        'folders': folders,
        'current_folder': current_folder,
        'breadcrumbs': breadcrumbs,
        'file_form': file_form,
        'folder_form': folder_form,
    }
    return render(request, 'file_save/file_list.html', context)

@login_required(login_url='usermanage:login')
@require_http_methods(["POST"])
def FileUpload(request):
    form = UploadedFileForm(request.POST, request.FILES, user=request.user)
    if form.is_valid():
        uploaded_file = form.save(commit=False)
        uploaded_file.owner = request.user
        uploaded_file.original_name = request.FILES['file'].name
        uploaded_file.file_size = request.FILES['file'].size
        uploaded_file.save()
        
        folder_id = request.POST.get('current_folder')
        if folder_id:
            return redirect(f'/file_save/file_list/?folder={folder_id}')
        return redirect('file_save:file_list')
    else:
        return HttpResponse(form.errors, status=400)

@login_required(login_url='usermanage:login')
@require_http_methods(["POST"])
def FileDelete(request, id):
    try:
        file_instance = get_object_or_404(UploadedFile, id=id, owner=request.user)
        folder_id = file_instance.folder.id if file_instance.folder else None
        file_instance.file.delete()  # 删除文件
        file_instance.delete()  # 删除数据库记录
        
        if folder_id:
            return redirect(f'/file_save/file_list/?folder={folder_id}')
        return redirect('file_save:file_list')
    except UploadedFile.DoesNotExist:
        return HttpResponse("文件未找到", status=404)

@login_required(login_url='usermanage:login')
@require_http_methods(["POST"])
def FolderCreate(request):
    form = FolderForm(request.POST)
    if form.is_valid():
        folder = form.save(commit=False)
        folder.owner = request.user
        
        parent_id = request.POST.get('parent_folder')
        if parent_id:
            folder.parent = get_object_or_404(Folder, id=parent_id, owner=request.user)
        
        try:
            folder.save()
            if parent_id:
                return redirect(f'/file_save/file_list/?folder={parent_id}')
            return redirect('file_save:file_list')
        except Exception as e:
            return HttpResponse(f"创建文件夹失败: {str(e)}", status=400)
    else:
        return HttpResponse(form.errors, status=400)

@login_required(login_url='usermanage:login')
@require_http_methods(["POST"])
def FolderDelete(request, id):
    try:
        folder = get_object_or_404(Folder, id=id, owner=request.user)
        parent_id = folder.parent.id if folder.parent else None
        folder.delete()  # 级联删除子文件夹和文件
        
        if parent_id:
            return redirect(f'/file_save/file_list/?folder={parent_id}')
        return redirect('file_save:file_list')
    except Folder.DoesNotExist:
        return HttpResponse("文件夹未找到", status=404)

@login_required(login_url='usermanage:login')
def FileDownload(request, id):
    """使用 nginx X-Accel-Redirect 进行高效下载"""
    file_instance = get_object_or_404(UploadedFile, id=id, owner=request.user)
    
    # 在开发环境中直接返回文件
    if settings.DEBUG:
        response = FileResponse(file_instance.file.open('rb'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{file_instance.original_name}"'
        return response
    
    # 在生产环境中使用 nginx X-Accel-Redirect
    file_path = file_instance.file.path
    # 将实际路径转换为 nginx 内部路径
    internal_path = file_path.replace(settings.MEDIA_ROOT, '/protected')
    
    response = HttpResponse()
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="{file_instance.original_name}"'
    response['X-Accel-Redirect'] = internal_path
    return response
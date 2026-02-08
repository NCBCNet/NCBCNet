from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import UploadedFile, Folder
from .forms import UploadedFileForm, FolderForm
from django.shortcuts import redirect
from django.db.models import Q
from asgiref.sync import sync_to_async
import os
import asyncio
from django.conf import settings

# Async file iterator for streaming downloads
async def async_file_iterator(file_object, chunk_size=8192):
    """Asynchronously iterate over file chunks"""
    while True:
        chunk = await sync_to_async(file_object.read)(chunk_size)
        if not chunk:
            break
        yield chunk

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
async def FileUpload(request):
    """异步文件上传视图"""
    # 使用 sync_to_async 处理表单验证
    form = await sync_to_async(UploadedFileForm)(
        request.POST, request.FILES, user=request.user
    )
    
    # 异步验证表单
    is_valid = await sync_to_async(form.is_valid)()
    
    if is_valid:
        # 异步保存文件
        uploaded_file = await sync_to_async(form.save)(commit=False)
        uploaded_file.owner = request.user
        uploaded_file.original_name = request.FILES['file'].name
        uploaded_file.file_size = request.FILES['file'].size
        
        # 异步保存到数据库
        await sync_to_async(uploaded_file.save)()
        
        folder_id = request.POST.get('current_folder')
        
        # 返回 JSON 响应给 AJAX 请求
        return JsonResponse({
            'success': True,
            'message': '文件上传成功',
            'file_id': uploaded_file.id,
            'file_name': uploaded_file.original_name,
            'redirect_url': f"{reverse('file_save:file_list')}?folder={folder_id}" if folder_id else reverse('file_save:file_list')
        })
    else:
        # 获取表单错误
        errors = await sync_to_async(lambda: form.errors.as_json())()
        return JsonResponse({
            'success': False,
            'message': '文件上传失败',
            'errors': errors
        }, status=400)

@login_required(login_url='usermanage:login')
@require_http_methods(["POST"])
def FileDelete(request, id):
    try:
        file_instance = get_object_or_404(UploadedFile, id=id, owner=request.user)
        folder_id = file_instance.folder.id if file_instance.folder else None
        file_instance.file.delete()  # 删除文件
        file_instance.delete()  # 删除数据库记录
        
        if folder_id:
            return redirect(f"{reverse('file_save:file_list')}?folder={folder_id}")
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
                return redirect(f"{reverse('file_save:file_list')}?folder={parent_id}")
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
            return redirect(f"{reverse('file_save:file_list')}?folder={parent_id}")
        return redirect('file_save:file_list')
    except Folder.DoesNotExist:
        return HttpResponse("文件夹未找到", status=404)

@login_required(login_url='usermanage:login')
async def FileDownload(request, id):
    """异步文件下载视图 - 使用 nginx X-Accel-Redirect 进行高效下载"""
    # 异步获取文件实例
    file_instance = await sync_to_async(get_object_or_404)(
        UploadedFile, id=id, owner=request.user
    )
    
    # 在开发环境中使用异步流式传输
    if settings.DEBUG:
        # 异步打开文件
        file_obj = await sync_to_async(file_instance.file.open)('rb')
        
        # 创建流式响应
        response = StreamingHttpResponse(
            async_file_iterator(file_obj),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{file_instance.original_name}"'
        response['Content-Length'] = file_instance.file_size
        return response
    
    # 在生产环境中使用 nginx X-Accel-Redirect（nginx 处理异步）
    file_path = await sync_to_async(lambda: file_instance.file.path)()
    # 使用 os.path.relpath 确保路径正确
    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
    internal_path = '/protected/' + relative_path.replace('\\', '/')  # 处理 Windows 路径
    
    response = HttpResponse()
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="{file_instance.original_name}"'
    response['X-Accel-Redirect'] = internal_path
    return response
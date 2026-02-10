from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse, StreamingHttpResponse,Http404
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import UploadedFile, Folder
from .forms import UploadedFileForm, FolderForm, FileShareForm
from django.shortcuts import redirect
from django.db.models import Q
from asgiref.sync import sync_to_async
import os
import asyncio
from urllib.parse import quote
from django.conf import settings
import aiofiles

# Async file iterator for streaming downloads
async def async_file_iterator(file_path, chunk_size=8192):
    async with aiofiles.open(file_path, 'rb') as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk

# Create your views here.
@login_required(login_url='usermanage:login')
async def FileList(request):
    if request.method == 'POST':
        shared_form = FileShareForm(request.POST)
        if shared_form.is_valid():
            file_id = shared_form.cleaned_data['shared_target']
            try:
                file_instance = await UploadedFile.objects.select_related('folder').aget(id=file_id, owner=request.user)
                file_instance.share = not file_instance.share
                await file_instance.asave()
                folder_id = file_instance.folder.id if file_instance.folder else None
                if folder_id:
                    return redirect(f"{reverse('file_save:file_list')}?folder={folder_id}")
                return redirect('file_save:file_list')
            except UploadedFile.DoesNotExist:
                raise Http404("文件不存在")
        else:
            return HttpResponse("无效的请求", status=400)
    else:
        form = FileShareForm()
        folders_count = 0
        files_count = 0
        folder_id = request.GET.get('folder')
        current_folder = None
        def query_shared_files():
            return UploadedFile.objects.filter(share=True).exclude(owner=request.user)
        shared_files = await sync_to_async(query_shared_files)()
        if folder_id:
            current_folder = get_object_or_404(Folder, id=folder_id, owner=request.user)

        # 获取当前文件夹下的子文件夹
        if current_folder:
            folders = Folder.objects.filter(parent=current_folder, owner=request.user)
            folders_count = await folders.acount()
        else:
            folders = Folder.objects.filter(parent=None, owner=request.user)
            folders_count = await folders.acount()

        # 获取当前文件夹下的文件
        if current_folder:
            files = UploadedFile.objects.filter(folder=current_folder, owner=request.user)
            files_count = await files.acount()
        else:
            files = UploadedFile.objects.filter(folder=None, owner=request.user)
            files_count = await files.acount()
        files_lenth = await sync_to_async(len)(files)
        # 获取面包屑导航
        breadcrumbs = []
        if current_folder:
            temp_folder = current_folder
            while temp_folder:
                breadcrumbs.insert(0, temp_folder)
                temp_folder = temp_folder.parent

        file_form = UploadedFileForm(user=request.user)
        folder_form = FolderForm()
        is_shared_files = await sync_to_async(shared_files.exists)()
        is_files = await sync_to_async(files.exists)() or await sync_to_async(folders.exists)()
        context = {
            'files': files,
            'folders': folders,
            'folders_count': folders_count,
            'files_count': files_count,
            'files_lenth': files_lenth,
            'current_folder': current_folder,
            'breadcrumbs': breadcrumbs,
            'file_form': file_form,
            'folder_form': folder_form,
            'share_form': form,
            'shared_files': shared_files,
            'is_shared_files': is_shared_files,
            'is_files': is_files,
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
        await uploaded_file.asave()
        
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
async def FileDelete(request, id):
    """异步文件删除视图"""
    try:
        # 异步获取文件实例，预加载folder关系
        file_instance = await UploadedFile.objects.select_related('folder').aget(id=id, owner=request.user)
        folder_id = file_instance.folder.id if file_instance.folder else None
        
        # 删除物理文件（同步操作，但在async视图中使用sync_to_async包装）
        await sync_to_async(file_instance.file.delete)()
        # 删除数据库记录
        await file_instance.adelete()
        
        if folder_id:
            return redirect(f"{reverse('file_save:file_list')}?folder={folder_id}")
        return redirect('file_save:file_list')
    except UploadedFile.DoesNotExist:
        return HttpResponse("文件未找到", status=404)

@login_required(login_url='usermanage:login')
@require_http_methods(["POST"])
async def FolderCreate(request):
    """异步文件夹创建视图"""
    # 直接从POST数据创建文件夹，不使用表单的save方法
    folder_name = request.POST.get('name', '').strip()
    
    if not folder_name:
        return HttpResponse("文件夹名称不能为空", status=400)
    
    # Get user asynchronously
    user = await sync_to_async(lambda: request.user)()
    
    # 创建文件夹对象
    folder = Folder(name=folder_name, owner=user)
    
    parent_id = request.POST.get('parent_folder')
    if parent_id:
        try:
            folder.parent = await Folder.objects.aget(id=parent_id, owner=user)
        except Folder.DoesNotExist:
            return HttpResponse("父文件夹未找到", status=404)
    
    try:
        await folder.asave()
        if parent_id:
            return redirect(f"{reverse('file_save:file_list')}?folder={parent_id}")
        return redirect('file_save:file_list')
    except Exception as e:
        return HttpResponse(f"创建文件夹失败: {str(e)}", status=400)

@login_required(login_url='usermanage:login')
@require_http_methods(["POST"])
async def FolderDelete(request, id):
    """异步文件夹删除视图"""
    try:
        # 异步获取文件夹实例，预加载parent关系
        folder = await Folder.objects.select_related('parent').aget(id=id, owner=request.user)
        parent_id = folder.parent.id if folder.parent else None
        
        # 使用sync_to_async包装delete方法，因为它可能涉及删除物理文件
        await sync_to_async(folder.delete)()
        
        if parent_id:
            return redirect(f"{reverse('file_save:file_list')}?folder={parent_id}")
        return redirect('file_save:file_list')
    except Folder.DoesNotExist:
        return HttpResponse("文件夹未找到", status=404)

@login_required(login_url='usermanage:login')
async def FileDownload(request, id):
    """异步文件下载视图 - 使用 nginx X-Accel-Redirect 进行高效下载"""
    # 异步获取文件实例，使用 select_related 预加载 owner
    try:
        file_instance = await UploadedFile.objects.select_related('owner').aget(id=id)
        if file_instance.share:
            pass
        elif file_instance.owner != request.user:
            return redirect('server:illegal_request')
    except UploadedFile.DoesNotExist:
        raise Http404("文件不存在")
    
    # Wrap file path access in sync_to_async
    file_path = await sync_to_async(lambda: file_instance.file.path)()
    # 获取原始文件名
    original_name = file_instance.original_name
    
    # 根据 RFC 5987 和 RFC 2231 编码文件名
    # filename 参数使用 ASCII 安全的名称作为后备
    # filename* 参数使用 UTF-8 编码的完整文件名
    encoded_filename = quote(original_name.encode('utf-8'), safe='')
    
    # 创建 ASCII 安全的后备文件名
    # 尝试提取文件扩展名
    if '.' in original_name:
        ext = original_name.rsplit('.', 1)[1]
        ascii_fallback = f"download.{ext}"
    else:
        ascii_fallback = "download"
    
    # 构建符合 RFC 5987 标准的 Content-Disposition 头
    # 注意：filename 参数不应包含非 ASCII 字符
    content_disposition = f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_filename}'
    
    # 在开发环境中使用异步流式传输
    if settings.DEBUG:
        
        # 创建流式响应
        response = StreamingHttpResponse(
            async_file_iterator(file_path),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = content_disposition
        response['Content-Length'] = file_instance.file_size
        return response

    # 使用 os.path.relpath 确保路径正确
    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
    internal_path = '/protected/' + relative_path.replace('\\', '/')  # 处理 Windows 路径
    
    response = HttpResponse()
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = content_disposition
    response['X-Accel-Redirect'] = internal_path
    return response

# @login_required(login_url='usermanage:login')
# async def switch_share(request, id):
#     try:
#         file_instance = await UploadedFile.objects.aget(id=id, owner=request.user)
#         file_instance.share = not file_instance.share
#         await file_instance.asave()
#         folder_id = file_instance.folder.id if file_instance.folder else None
#         if folder_id:
#             return redirect(f"{reverse('file_save:file_list')}?folder={folder_id}")
#         return redirect('file_save:file_list')
#     except UploadedFile.DoesNotExist:
#         raise Http404("文件不存在")
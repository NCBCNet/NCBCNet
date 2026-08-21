"""file_save 业务服务层（阶段二 M2：模块化单体）。

约定：所有 ORM 操作与事务边界（transaction.atomic）都收敛在本层，
api 视图只做请求解析 / 序列化 / 响应组装，不再直接触碰模型。
"""
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from file_save.models import Folder, UploadedFile


# ---------------------------------------------------------------------------
# 文件夹
# ---------------------------------------------------------------------------
def list_folders(user, parent_id=None):
    """用户文件夹列表：parent_id 存在时列出子文件夹，否则列出顶层文件夹。"""
    queryset = Folder.objects.filter(owner=user)
    if parent_id:
        return queryset.filter(parent_id=parent_id)
    return queryset.filter(parent=None)


def create_folder(user, name, parent=None):
    """创建文件夹（事务内）。"""
    with transaction.atomic():
        return Folder.objects.create(owner=user, name=name, parent=parent)


def delete_folder(user, folder_id):
    """删除文件夹（模型 delete 会递归清理子文件夹与物理文件，事务内）。"""
    with transaction.atomic():
        folder = get_object_or_404(Folder, pk=folder_id, owner=user)
        folder.delete()
        return folder


# ---------------------------------------------------------------------------
# 文件
# ---------------------------------------------------------------------------
def list_files(user, folder_id=None, shared=False):
    """文件列表：shared=True 返回他人共享文件；否则按 folder_id 过滤。"""
    if shared:
        return UploadedFile.objects.filter(share=True).exclude(owner=user)
    queryset = UploadedFile.objects.filter(owner=user)
    if folder_id:
        return queryset.filter(folder_id=folder_id)
    return queryset.filter(folder=None)


def list_shared_files(user):
    """其他用户共享的文件列表。"""
    return UploadedFile.objects.filter(share=True).exclude(owner=user)


def upload_file(user, file_obj, folder=None, original_name=None, file_size=0):
    """保存上传文件记录（事务内）。"""
    with transaction.atomic():
        return UploadedFile.objects.create(
            owner=user,
            file=file_obj,
            folder=folder,
            original_name=original_name or getattr(file_obj, 'name', ''),
            file_size=file_size,
        )


def delete_file(user, file_id):
    """删除文件（同时删除物理文件，事务内）。"""
    with transaction.atomic():
        file_instance = get_object_or_404(UploadedFile, pk=file_id, owner=user)
        if file_instance.file:
            file_instance.file.delete(save=False)
        file_instance.delete()
        return file_instance


def toggle_share(user, file_id):
    """切换文件共享状态（仅所有者，事务内）。"""
    try:
        file_instance = UploadedFile.objects.get(pk=file_id, owner=user)
    except UploadedFile.DoesNotExist:
        raise Http404('文件不存在')
    with transaction.atomic():
        file_instance.share = not file_instance.share
        file_instance.save(update_fields=['share'])
        return file_instance


# ---------------------------------------------------------------------------
# 下载授权
# ---------------------------------------------------------------------------
def get_file(file_id):
    """按 id 取文件（不存在则 404），不校验所有权。

    供签名下载端点使用：签名本身即授权凭证。
    """
    return get_object_or_404(UploadedFile, pk=file_id)


def get_downloadable_file(user, file_id):
    """返回当前用户可下载的文件（所有者或共享文件），否则拒绝。"""
    file_instance = get_object_or_404(UploadedFile, pk=file_id)
    if file_instance.owner_id != user.id and not file_instance.share:
        raise PermissionDenied('无权下载该文件')
    return file_instance

from django.contrib import admin
from .models import Folder, UploadedFile
# Register your models here.
admin.site.register(Folder)
admin.site.register(UploadedFile)
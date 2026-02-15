from django import forms
from .models import UploadedFile, Folder

class UploadedFileForm(forms.ModelForm):
    folder = forms.ModelChoiceField(
        queryset=Folder.objects.none(),
        required=False,
        empty_label="根目录",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = UploadedFile
        fields = ['file', 'folder']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['folder'].queryset = Folder.objects.filter(owner=user)

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '文件夹名称'})
        }

class FileShareForm(forms.Form):
    shared_target = forms.IntegerField(widget=forms.HiddenInput())
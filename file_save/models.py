from django.db import models

# Create your models here.
class UploadedFile(models.Model):
    # title = models.CharField(max_length=100, blank=True)
    # description = models.CharField(max_length=255, blank=True)
    file = models.FileField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-uploaded_at']
    def __str__(self):
        return self.file.name
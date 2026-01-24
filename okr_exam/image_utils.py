"""
图片分割工具模块
用于处理扫描试卷图片的分割
"""
from PIL import Image
from django.core.files.base import ContentFile
import io


def segment_exam_image(submission):
    """
    分割扫描试卷图片
    根据试卷各分节定义的区域坐标，从原始扫描图片中裁剪出各个答题区域
    
    Args:
        submission: ExamSubmission对象，需要包含scanned_image
    
    Returns:
        list: 创建的ImageSegment对象列表
    """
    from .models import ImageSegment
    
    if not submission.scanned_image:
        return []
    
    # 打开原始扫描图片
    img = Image.open(submission.scanned_image.path)
    img_width, img_height = img.size
    
    segments = []
    
    # 遍历试卷的所有分节
    for section in submission.paper.sections.all():
        # 将百分比坐标转换为像素坐标
        x = int(img_width * section.region_x / 100)
        y = int(img_height * section.region_y / 100)
        width = int(img_width * section.region_width / 100)
        height = int(img_height * section.region_height / 100)
        
        # 裁剪图片
        box = (x, y, x + width, y + height)
        cropped_img = img.crop(box)
        
        # 保存裁剪后的图片
        output = io.BytesIO()
        cropped_img.save(output, format='PNG')
        output.seek(0)
        
        # 创建ImageSegment对象
        segment = ImageSegment.objects.create(
            submission=submission,
            section=section,
            x=x,
            y=y,
            width=width,
            height=height
        )
        
        # 保存图片文件
        filename = f'submission_{submission.id}_section_{section.id}.png'
        segment.segment_image.save(filename, ContentFile(output.read()), save=True)
        
        segments.append(segment)
    
    # 标记提交为已分割
    submission.is_segmented = True
    submission.save()
    
    return segments


def create_preview_image(image_path, max_width=800):
    """
    创建图片预览（缩小图片以便在网页上显示）
    
    Args:
        image_path: 图片路径
        max_width: 最大宽度
    
    Returns:
        BytesIO: 处理后的图片数据
    """
    img = Image.open(image_path)
    
    # 计算缩放比例
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    
    return output

"""可插拔的 OCR/OMR 识别适配器。

生产环境可安装 pytesseract/opencv-python 后启用对应引擎；未安装时使用
显式的 unavailable 结果，不能伪造识别成功。
"""
from io import BytesIO
import os


class OCRAdapter:
    name = "base"

    def recognize(self, image_bytes):
        raise NotImplementedError


class OMRAdapter:
    name = "base"

    def recognize(self, image_bytes, regions):
        raise NotImplementedError


class BarcodeAdapter:
    name = "base"

    def recognize(self, image_bytes):
        raise NotImplementedError


class UnavailableBarcodeAdapter(BarcodeAdapter):
    name = "unavailable"

    def recognize(self, image_bytes):
        return {
            "values": [],
            "confidence": 0,
            "engine": self.name,
            "status": "unavailable",
            "needs_review": True,
        }


class OpenCVBarcodeAdapter(BarcodeAdapter):
    name = "opencv-qr"

    def recognize(self, image_bytes):
        import cv2
        import numpy as np

        image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if image is not None and min(image.shape[:2]) < 200:
            scale = max(2, int(200 / min(image.shape[:2])))
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        detector = cv2.QRCodeDetector()
        value, _, _ = detector.detectAndDecode(image)
        values = [value] if value else []
        return {
            "values": values,
            "confidence": 1 if values else 0,
            "engine": self.name,
            "status": "completed" if values else "not_found",
            "needs_review": not bool(values),
        }


class PyzbarBarcodeAdapter(BarcodeAdapter):
    name = "pyzbar"

    def recognize(self, image_bytes):
        from PIL import Image
        from pyzbar.pyzbar import decode

        with Image.open(BytesIO(image_bytes)) as image:
            decoded = decode(image)
        values = [item.data.decode("utf-8", errors="replace").strip() for item in decoded if item.data]
        values = [value for value in values if value]
        return {
            "values": values,
            "confidence": 1 if values else 0,
            "engine": self.name,
            "status": "completed" if values else "not_found",
            "needs_review": not bool(values),
        }


class HybridBarcodeAdapter(BarcodeAdapter):
    name = "hybrid-barcode"

    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    def recognize(self, image_bytes):
        primary_result = self.primary.recognize(image_bytes)
        if primary_result.get("values"):
            return primary_result
        fallback_result = self.fallback.recognize(image_bytes)
        if fallback_result.get("values"):
            return fallback_result
        return {
            **primary_result,
            "fallback": fallback_result,
            "engine": self.name,
            "needs_review": True,
        }


class UnavailableOCRAdapter(OCRAdapter):
    name = "unavailable"

    def recognize(self, image_bytes):
        return {
            "text": None,
            "confidence": 0,
            "engine": self.name,
            "status": "unavailable",
            "needs_review": True,
        }


class TesseractOCRAdapter(OCRAdapter):
    name = "tesseract"

    def recognize(self, image_bytes):
        import pytesseract
        from PIL import Image

        with Image.open(BytesIO(image_bytes)) as image:
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                lang=os.getenv("GRADING_OCR_LANG", "eng"),
            )
        values = [text.strip() for text in data.get("text", []) if text.strip()]
        confidences = [
            float(value) for value in data.get("conf", [])
            if str(value).strip() not in {"", "-1"}
        ]
        confidence = round(sum(confidences) / len(confidences) / 100, 4) if confidences else 0
        minimum_confidence = float(os.getenv("GRADING_OCR_MIN_CONFIDENCE", "0.85"))
        return {
            "text": " ".join(values) or None,
            "confidence": confidence,
            "engine": self.name,
            "status": "completed",
            "needs_review": confidence < minimum_confidence,
        }


class UnavailableOMRAdapter(OMRAdapter):
    name = "unavailable"

    def recognize(self, image_bytes, regions):
        minimum_mark_ratio = float(os.getenv("GRADING_OMR_MIN_MARK_RATIO", "0.1"))
        return {
            "answers": [],
            "regions": len(regions),
            "confidence": 0,
            "engine": self.name,
            "status": "unavailable",
            "needs_review": bool(regions),
        }


class OpenCVOMRAdapter(OMRAdapter):
    name = "opencv"

    def recognize(self, image_bytes, regions):
        import cv2
        import numpy as np

        image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if image is None:
            return {
                "answers": [],
                "regions": len(regions),
                "confidence": 0,
                "engine": self.name,
                "status": "failed",
                "needs_review": True,
            }
        answers = []
        confidences = []
        margins = []
        for region in regions:
            options = region.get("options", [])
            values = []
            for option in options:
                x, y, width, height = [int(value) for value in option["bbox"]]
                crop = image[y:y + height, x:x + width]
                if crop.size == 0:
                    continue
                threshold = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                ratio = float(np.count_nonzero(threshold)) / threshold.size
                values.append({"key": option.get("key"), "mark_ratio": round(ratio, 4)})
            if values:
                values.sort(key=lambda item: item["mark_ratio"], reverse=True)
                selected = values[0]
                answers.append({"question": region.get("question"), "selected": selected["key"], "options": values})
                confidences.append(selected["mark_ratio"])
                margins.append(
                    round(selected["mark_ratio"] - values[1]["mark_ratio"], 4)
                    if len(values) > 1 else selected["mark_ratio"]
                )
        confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0
        minimum_mark_ratio = float(os.getenv("GRADING_OMR_MIN_MARK_RATIO", "0.1"))
        minimum_margin = float(os.getenv("GRADING_OMR_MIN_MARGIN", "0.15"))
        ambiguous = any(margin < minimum_margin for margin in margins)
        return {
            "answers": answers,
            "regions": len(regions),
            "confidence": confidence,
            "minimum_margin": minimum_margin,
            "ambiguous": ambiguous,
            "engine": self.name,
            "status": "completed",
            "needs_review": confidence < minimum_mark_ratio or ambiguous,
        }


def get_ocr_adapter():
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return UnavailableOCRAdapter()
    return TesseractOCRAdapter()


def get_omr_adapter():
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        return UnavailableOMRAdapter()
    return OpenCVOMRAdapter()


def get_barcode_adapter():
    opencv_available = False
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        pass
    else:
        opencv_available = True

    pyzbar_available = False
    try:
        import pyzbar  # noqa: F401
    except (ImportError, OSError):
        pass
    else:
        pyzbar_available = True

    if opencv_available and pyzbar_available:
        return HybridBarcodeAdapter(OpenCVBarcodeAdapter(), PyzbarBarcodeAdapter())
    if opencv_available:
        return OpenCVBarcodeAdapter()
    if pyzbar_available:
        return PyzbarBarcodeAdapter()
    return UnavailableBarcodeAdapter()

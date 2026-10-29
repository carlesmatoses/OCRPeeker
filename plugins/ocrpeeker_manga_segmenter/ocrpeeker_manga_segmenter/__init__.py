from PIL import Image

from ocrpeeker import config
from ocrpeeker.segmenter.base import Box, Segmenter, normalize_xyxy

MODEL_ID = "ogkalu/comic-text-and-bubble-detector"

# The model also detects whole speech bubbles ("bubble"); only the text
# regions are wanted, whether inside a bubble or floating on the art.
TEXT_LABELS = {"text_bubble", "text_free"}


class MangaSegmenter(Segmenter):
    """Finds text regions on manga/comic pages with an RT-DETR detector."""

    def __init__(self):
        import torch
        from transformers import (
            AutoImageProcessor,
            AutoModelForObjectDetection,
        )

        self._torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = AutoImageProcessor.from_pretrained(MODEL_ID)
        self.model = (
            AutoModelForObjectDetection.from_pretrained(MODEL_ID)
            .to(self.device)
            .eval()
        )
        self.threshold = float(
            config.get_or_default(config.SEGMENTER_CONFIG, "threshold")
        )
        self.text_label_ids = {
            int(i)
            for i, label in self.model.config.id2label.items()
            if label in TEXT_LABELS
        }

    def segment(self, image: Image.Image) -> list[Box]:
        inputs = self.processor(images=image, return_tensors="pt").to(
            self.device
        )
        with self._torch.inference_mode():
            outputs = self.model(**inputs)

        width, height = image.size
        result = self.processor.post_process_object_detection(
            outputs, threshold=self.threshold, target_sizes=[(height, width)]
        )[0]

        return [
            normalize_xyxy(*box.tolist(), width=width, height=height)
            for label, box in zip(result["labels"].tolist(), result["boxes"])
            if label in self.text_label_ids
        ]

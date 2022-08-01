import os
import time
import warnings

import cv2
import torch
from builtins import print

from docarray import DocumentArray
from torch.backends import cudnn
import torch.nn.functional as nn

from marie import Executor, requests, __model_path__, __marie_home__
from marie.executor.ner.utils import (
    normalize_bbox,
    unnormalize_box,
    iob_to_label,
    get_font,
    get_random_color,
    draw_box,
    visualize_icr,
    visualize_prediction,
    visualize_extract_kv,
)

from marie.logging.logger import MarieLogger
from marie.timer import Timer
from marie.utils.utils import ensure_exists
from marie.utils.overlap import find_overlap_horizontal
from marie.utils.overlap import merge_bboxes_as_block

from PIL import Image, ImageDraw, ImageFont
import logging
from typing import Optional, List, Any, Tuple, Dict, Union

import numpy as np

from PIL import Image
from transformers import AutoModelForTokenClassification, AutoProcessor

from transformers import (
    LayoutLMv3Processor,
    LayoutLMv3FeatureExtractor,
    LayoutLMv3ForTokenClassification,
    LayoutLMv3TokenizerFast,
)


from transformers.utils import check_min_version

# Will error if the minimal version of Transformers is not installed. Remove at your own risks.
from marie.boxes.line_processor import find_line_number
from marie.executor import TextExtractionExecutor
from marie.executor.text_extraction_executor import CoordinateFormat
from marie.utils.docs import (
    docs_from_file,
    array_from_docs,
    docs_from_image,
    load_image,
    convert_frames,
)

from marie.utils.image_utils import viewImage, read_image, hash_file
from marie.utils.json import store_json_object, load_json_file
from pathlib import Path

# Calling this from here prevents : "AttributeError: module 'detectron2' has no attribute 'config'"
from detectron2.config import get_cfg

check_min_version("4.5.0")
logger = logging.getLogger(__name__)


def obtain_ocr(src_image: str, text_executor: TextExtractionExecutor):
    """
    Obtain OCR words
    """
    docs = docs_from_file(src_image)
    frames = array_from_docs(docs)
    kwa = {"payload": {"output": "json", "mode": "sparse", "format": "xyxy"}}
    results = text_executor.extract(docs, **kwa)

    return results, frames


class NerExtractionExecutor(Executor):
    """
    Executor for extracting text.
    Text extraction can either be executed out over the entire image or over selected regions of interests (ROIs)
    aka bounding boxes.
    """

    def __init__(
        self, pretrained_model_name_or_path: Optional[Union[str, os.PathLike]], **kwargs
    ):
        super().__init__(**kwargs)
        self.show_error = True  # show prediction errors
        self.logger = MarieLogger(
            getattr(self.metas, "name", self.__class__.__name__)
        ).logger

        self.logger.info(f"NER Extraction Executor : {pretrained_model_name_or_path}")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # sometimes we have CUDA/GPU support but want to only use CPU
        use_cuda = torch.cuda.is_available()
        if os.environ.get("MARIE_DISABLE_CUDA"):
            use_cuda = False
            self.device = "cpu"

        if use_cuda:
            try:
                from torch._C import _cudnn

                # It seems good practice to turn off cudnn.benchmark when turning on cudnn.deterministic
                cudnn.benchmark = True
                cudnn.deterministic = False
            except ImportError:
                pass

        ensure_exists("/tmp/tensors")
        ensure_exists("/tmp/tensors/json")

        pretrained_model_name_or_path = str(pretrained_model_name_or_path)

        if os.path.isfile(pretrained_model_name_or_path):
            warnings.warn("Expected model directory")

        config_path = os.path.join(pretrained_model_name_or_path, "config.ner.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError("Expected config.ner.json not found")

        self.init_configuration = load_json_file(config_path)

        self.debug_visuals = self.init_configuration["debug"]["visualize"]["enabled"]
        self.debug_visuals_overlay = self.init_configuration["debug"]["visualize"][
            "overlay"
        ]
        self.debug_visuals_icr = self.init_configuration["debug"]["visualize"]["icr"]
        self.debug_visuals_ner = self.init_configuration["debug"]["visualize"]["ner"]
        self.debug_visuals_prediction = self.init_configuration["debug"]["visualize"][
            "prediction"
        ]

        self.debug_scores = self.init_configuration["debug"]["scores"]
        self.debug_colors = self.init_configuration["debug"]["colors"]

        self.model = self.__load_model(pretrained_model_name_or_path, self.device)
        self.processor = self.__create_processor()
        self.text_executor: Optional[TextExtractionExecutor] = TextExtractionExecutor()

    def __create_processor(self):
        """prepare for the model"""
        # Method:2 Create Layout processor with custom future extractor
        # Max model size is 512, so we will need to handle any documents larger than that
        feature_extractor = LayoutLMv3FeatureExtractor(apply_ocr=False)
        tokenizer = LayoutLMv3TokenizerFast.from_pretrained(
            "microsoft/layoutlmv3-large"
            # only_label_first_subword = True
        )
        processor = LayoutLMv3Processor(
            feature_extractor=feature_extractor, tokenizer=tokenizer
        )

        return processor

    def __load_model(self, model_dir: str, device: str):
        """
        Create token classification model
        """
        labels, _, _ = self.get_label_info()
        model = AutoModelForTokenClassification.from_pretrained(
            model_dir, num_labels=len(labels)
        )

        model.to(device)
        return model

    def get_label_info(self):
        labels = self.init_configuration["labels"]
        logger.info(f"Labels : {labels}")

        id2label = {v: k for v, k in enumerate(labels)}
        label2id = {k: v for v, k in enumerate(labels)}

        return labels, id2label, label2id

    def info(self, **kwargs):
        logger.info(f"Self : {self}")
        return {"index": "ner-complete"}

    def _filter(
        self, values: List[Any], probabilities: List[float], threshold: float
    ) -> List[Any]:
        return [
            value for probs, value in zip(probabilities, values) if probs >= threshold
        ]

    def inference(
        self,
        image: Any,
        words: List[Any],
        boxes: List[Any],
        labels: List[str],
        threshold: float,
    ) -> Tuple[List, List, List]:
        """Run Inference on the model with given processor"""
        logger.info(f"Performing inference")
        model = self.model
        processor = self.processor
        device = self.device
        id2label = {v: k for v, k in enumerate(labels)}

        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        logger.info(
            f"Tokenizer parallelism: {os.environ.get('TOKENIZERS_PARALLELISM', 'true')}"
        )

        width, height = image.size
        # Encode the image
        encoding = processor(
            # fmt: off
            image,
            words,
            boxes=boxes,
            truncation=True,
            return_offsets_mapping=True,
            padding="max_length",
            return_tensors="pt"
            # fmt: on
        )
        offset_mapping = encoding.pop("offset_mapping")

        # Debug tensor info
        if self.debug_visuals:
            # img_tensor = encoded_inputs["image"] # v2
            img_tensor = encoding["pixel_values"]  # v3
            img = Image.fromarray(
                (img_tensor[0].cpu()).numpy().astype(np.uint8).transpose(1, 2, 0)
            )
            # img.save(f"/tmp/tensors/tensor_{file_hash}_{frame_idx}.png")

        # ensure proper device placement
        for ek, ev in encoding.items():
            encoding[ek] = ev.to(device)

        # Perform forward pass
        with torch.no_grad():
            outputs = model(**encoding)
            # Get the predictions and probabilities
            probs = (
                nn.softmax(outputs.logits.squeeze(), dim=1).max(dim=1).values.tolist()
            )
            _predictions = outputs.logits.argmax(-1).squeeze().tolist()
            _token_boxes = encoding.bbox.squeeze().tolist()
            normalized_logits = outputs.logits.softmax(dim=-1).squeeze().tolist()

        # TODO : Filer the results
        # Filter the predictions and bounding boxes based on a threshold
        # predictions = _filter(_predictions, probs, threshold)
        # token_boxes = _filter(_token_boxes, probs, threshold)
        predictions = _predictions
        token_boxes = _token_boxes

        # Only keep non-subword predictions
        is_subword = np.array(offset_mapping.squeeze().tolist())[:, 0] != 0
        true_predictions = [
            id2label[pred]
            for idx, pred in enumerate(predictions)
            if not is_subword[idx]
        ]

        true_boxes = [
            unnormalize_box(box, width, height)
            for idx, box in enumerate(token_boxes)
            if not is_subword[idx]
        ]

        true_scores = [
            round(normalized_logits[idx][val], 6)
            for idx, val in enumerate(predictions)
            if not is_subword[idx]
        ]

        assert len(true_predictions) == len(true_boxes) == len(true_scores)

        predictions = [true_predictions]
        boxes = [true_boxes]
        scores = [true_scores]

        return predictions, boxes, scores

    def postprocess(self, frames, annotations, ocr_results, file_hash):
        """Post-process extracted data"""
        assert len(annotations) == len(ocr_results) == len(frames)

        # need to normalize all data from XYXY to XYWH as the NER process required XYXY and assets were saved XYXY format
        logger.info("Changing coordinate format from xyxy->xyhw")

        for data in ocr_results:
            for word in data["words"]:
                word["box"] = CoordinateFormat.convert(
                    word["box"], CoordinateFormat.XYXY, CoordinateFormat.XYWH
                )

        for data in annotations:
            for i, box in enumerate(data["boxes"]):
                box = CoordinateFormat.convert(
                    box, CoordinateFormat.XYXY, CoordinateFormat.XYWH
                )
                data["boxes"][i] = box

        aggregated_ner = []
        aggregated_kv = []
        aggregated_meta = []

        # expected NER and key/value pairs
        expected_ner = self.init_configuration["expected_ner"]
        expected_keys = self.init_configuration["expected_keys"]
        expected_pair = self.init_configuration["expected_pair"]

        for i, (ocr, annotation, frame) in enumerate(
            zip(ocr_results, annotations, frames)
        ):
            logger.info(f"Processing page # {i}")
            # lines and boxes are already in the right reading order TOP->BOTTOM, LEFT-TO-RIGHT so no need to sort
            lines_bboxes = np.array(ocr["meta"]["lines_bboxes"])
            true_predictions = annotation["predictions"]
            true_boxes = annotation["boxes"]
            true_scores = annotation["scores"]

            viz_img = frame.copy()
            draw = ImageDraw.Draw(viz_img, "RGBA")
            font = get_font(14)
            # aggregate prediction by their line numbers

            groups = {}
            for pred_idx, (prediction, pred_box, pred_score) in enumerate(
                zip(true_predictions, true_boxes, true_scores)
            ):
                # discard 'O' other
                label = prediction[2:]
                if not label:
                    continue
                # two labels that need to be removed [0.0, 0.0, 0.0, 0.0]  [2578.0, 3 3292.0, 0.0, 0.0]
                if np.array_equal(pred_box, [0.0, 0.0, 0.0, 0.0]) or (
                    pred_box[2] == 0 and pred_box[3] == 0
                ):
                    continue

                line_number = find_line_number(lines_bboxes, pred_box)
                if line_number not in groups:
                    groups[line_number] = []
                groups[line_number].append(pred_idx)

            # aggregate boxes into key/value pairs via simple state machine for each line
            aggregated_keys = {}

            for line_idx, line_box in enumerate(lines_bboxes):
                if line_idx not in groups:
                    logger.debug(
                        f"Line does not have any groups : {line_idx} : {line_box}"
                    )
                    continue

                prediction_indexes = np.array(groups[line_idx])
                line_aggregator = []

                for key in expected_keys:
                    spans = []
                    skip_to = -1
                    for m in range(0, len(prediction_indexes)):
                        if skip_to != -1 and m <= skip_to:
                            continue
                        pred_idx = prediction_indexes[m]
                        prediction = true_predictions[pred_idx]
                        label = prediction[2:]
                        aggregator = []

                        if label == key:
                            for n in range(m, len(prediction_indexes)):
                                pred_idx = prediction_indexes[n]
                                prediction = true_predictions[pred_idx]
                                label = prediction[2:]
                                if label != key:
                                    break
                                aggregator.append(pred_idx)
                                skip_to = n

                        if len(aggregator) > 0:
                            spans.append(aggregator)

                    if len(spans) > 0:
                        line_aggregator.append({"key": key, "groups": spans})

                true_predictions = np.array(true_predictions)
                true_boxes = np.array(true_boxes)
                true_scores = np.array(true_scores)

                for line_agg in line_aggregator:
                    field = line_agg["key"]
                    group_indexes = line_agg["groups"]

                    for group_index in group_indexes:
                        bboxes = true_boxes[group_index]
                        scores = true_scores[group_index]
                        group_score = round(np.average(scores), 6)
                        # create a bounding box around our blocks which could be possibly overlapping or being split
                        group_bbox = merge_bboxes_as_block(bboxes)

                        key_result = {
                            "line": line_idx,
                            "key": field,
                            "bbox": group_bbox,
                            "score": group_score,
                        }

                        if line_idx not in aggregated_keys:
                            aggregated_keys[line_idx] = []
                        aggregated_keys[line_idx].append(key_result)

                        if self.debug_visuals:
                            color_map = self.init_configuration["debug"]["colors"]
                            color = (
                                color_map[field]
                                if field in color_map
                                else get_random_color()
                            )

                            draw_box(
                                draw,
                                group_bbox,
                                None,
                                color,
                                font,
                            )

            # check if we have possible overlaps when there is a mislabeled token, this could be a flag
            # Strategy used here is a horizontal overlap, if we have it then we will aggregate them
            # B-PAN I-PAN I-PAN B-PAN-ANS I-PAN
            if self.init_configuration["mislabeled_token_strategy"] == "aggregate":
                for key in expected_keys:
                    for ag_key in aggregated_keys.keys():
                        row_items = aggregated_keys[ag_key]
                        bboxes = [row["bbox"] for row in row_items if row["key"] == key]
                        visited = [False for _ in range(0, len(bboxes))]
                        to_merge = {}

                        for idx in range(0, len(bboxes)):
                            if visited[idx]:
                                continue
                            visited[idx] = True
                            box = bboxes[idx]
                            overlaps, indexes, scores = find_overlap_horizontal(
                                box, bboxes
                            )
                            to_merge[ag_key] = [idx]

                            for _, overlap_idx in zip(overlaps, indexes):
                                visited[overlap_idx] = True
                                to_merge[ag_key].append(overlap_idx)

                        for _k, idxs in to_merge.items():
                            items = aggregated_keys[_k]
                            items = np.array(items)
                            # there is nothing to merge, except the original block
                            if len(idxs) == 1:
                                continue

                            idxs = np.array(idxs)
                            picks = items[idxs]
                            remaining = np.delete(items, idxs)

                            score_avg = round(
                                np.average([item["score"] for item in picks]), 6
                            )
                            block = merge_bboxes_as_block(
                                [item["bbox"] for item in picks]
                            )

                            new_item = picks[0]
                            new_item["score"] = score_avg
                            new_item["bbox"] = block

                            aggregated_keys[_k] = np.concatenate(
                                ([new_item], remaining)
                            )

            # expected fields groups that indicate that the field could have been present
            # but it might not have been associated with KV pair mapping, does not apply to NER

            possible_fields = self.init_configuration["possible_fields"]
            possible_field_meta = {}

            for field in possible_fields.keys():
                fields = possible_fields[field]
                possible_field_meta[field] = {"page": i, "found": False, "fields": []}
                for k in aggregated_keys.keys():
                    ner_keys = aggregated_keys[k]
                    for ner_key in ner_keys:
                        key = ner_key["key"]
                        if key in fields:
                            possible_field_meta[field]["found"] = True
                            possible_field_meta[field]["fields"].append(key)

            aggregated_meta.append({"page": i, "fields": possible_field_meta})

            # Aggregate KV pairs, this can overlap with NER tags so caution need to be taken
            for pair in expected_pair:
                expected_question = pair[0]
                expected_answer = pair[1]

                for k in aggregated_keys.keys():
                    ner_keys = aggregated_keys[k]

                    found_key = None
                    found_val = None

                    for ner_key in ner_keys:
                        key = ner_key["key"]
                        if expected_question == key:
                            found_key = ner_key
                            continue
                        # find the first match
                        if found_key is not None and found_val is None:
                            # find the first match
                            for exp_key in expected_answer:
                                if key in exp_key:
                                    found_val = ner_key
                                    break

                            if found_val is not None:
                                bbox_q = found_key["bbox"]
                                bbox_a = found_val["bbox"]

                                if bbox_a[0] < bbox_q[0]:
                                    logger.warning(
                                        "Answer is not on the right of question"
                                    )
                                    continue

                                category = found_key["key"]
                                kv_result = {
                                    "page": i,
                                    "category": category,
                                    "value": {
                                        "question": found_key,
                                        "answer": found_val,
                                    },
                                }

                                aggregated_kv.append(kv_result)

            # Collect NER tags
            for tag in expected_ner:
                for k in aggregated_keys.keys():
                    ner_keys = aggregated_keys[k]
                    for ner_key in ner_keys:
                        key = ner_key["key"]
                        if key == tag:
                            ner_result = {
                                "page": i,
                                "category": tag,
                                "value": {
                                    "answer": ner_key,
                                },
                            }
                            aggregated_ner.append(ner_result)

            if self.debug_visuals and self.debug_visuals_overlay:
                viz_img.save(f"/tmp/tensors/extract_{file_hash}_{i}.png")

        self.decorate_aggregates_with_text(aggregated_ner, frames)
        self.decorate_aggregates_with_text(aggregated_kv, frames)

        # visualize results per page
        if self.debug_visuals and self.debug_visuals_ner:
            for k in range(0, len(frames)):
                output_filename = f"/tmp/tensors/ner_{file_hash}_{k}.png"
                items = []
                items.extend([row for row in aggregated_kv if int(row["page"]) == k])
                items.extend([row for row in aggregated_ner if int(row["page"]) == k])
                visualize_extract_kv(output_filename, frames[k], items)

        results = {"meta": aggregated_meta, "kv": aggregated_kv, "ner": aggregated_ner}

        print(results)
        return results

    def decorate_aggregates_with_text(self, aggregated_kv, frames):
        """Decorate our answers with proper TEXT"""
        regions = []

        def create_region(field_id, page_index, bbox):
            box = np.array(bbox).astype(np.int32)
            x, y, w, h = box
            return {
                "id": field_id,
                "pageIndex": page_index,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
            }

        # performing secondary OCR yields much better results as we are using RAW-LINE as our segmentation method
        # aggregate results for OCR extraction
        for k, agg_result in enumerate(aggregated_kv):
            page_index = int(agg_result["page"])
            category = agg_result["category"]

            if "question" in agg_result["value"]:
                regions.append(
                    create_region(
                        f"{category}_{k}_k",
                        page_index,
                        agg_result["value"]["question"]["bbox"],
                    )
                )

            if "answer" in agg_result["value"]:
                regions.append(
                    create_region(
                        f"{category}_{k}_v",
                        page_index,
                        agg_result["value"]["answer"]["bbox"],
                    )
                )

        kwa = {
            "payload": {
                "output": "json",
                "mode": "raw_line",
                "format": "xywh",
                "filter_snippets": True,
                "regions": regions,
            }
        }

        # nothing to decorate
        if len(regions) == 0:
            return

        region_results = self.text_executor.extract(docs_from_image(frames), **kwa)
        # possible failure in extracting data for region
        if "regions" not in region_results:
            logger.warning("No regions returned")
            return
        region_results = region_results["regions"]

        # merge results
        for k, agg_result in enumerate(aggregated_kv):
            category = agg_result["category"]
            for region in region_results:
                rid = region["id"]
                if rid == f"{category}_{k}_k":
                    agg_result["value"]["question"]["text"] = {
                        "text": region["text"],
                        "confidence": region["confidence"],
                    }
                if rid == f"{category}_{k}_v":
                    agg_result["value"]["answer"]["text"] = {
                        "text": region["text"],
                        "confidence": region["confidence"],
                    }

    def preprocess(self, src_image: str):
        """Pre-process src image for NER extraction"""

        if not os.path.exists(src_image):
            print(f"File not found : {src_image}")
            return

        # Obtain OCR results
        file_hash = hash_file(src_image)
        root_dir = __marie_home__

        ensure_exists(os.path.join(root_dir, "ocr"))
        ensure_exists(os.path.join(root_dir, "annotation"))

        ocr_json_path = os.path.join(root_dir, "ocr", f"{file_hash}.json")
        annotation_json_path = os.path.join(root_dir, "annotation", f"{file_hash}.json")

        print(f"Root      : {root_dir}")
        print(f"SrcImg    : {src_image}")
        print(f"Hash      : {file_hash}")
        print(f"OCR file  : {ocr_json_path}")
        print(f"NER file  : {annotation_json_path}")

        if not os.path.exists(ocr_json_path) and self.text_executor is None:
            raise Exception(f"OCR File not found : {ocr_json_path}")

        loaded, frames = load_image(src_image, img_format="pil")
        if not loaded:
            raise Exception(f"Unable to load image file: {src_image}")
        ocr_results = {}
        if os.path.exists(ocr_json_path):
            ocr_results = load_json_file(ocr_json_path)
            if "error" in ocr_results:
                msg = ocr_results["error"]
                logger.info(f"Retrying document > {file_hash} due to : {msg}")
                os.remove(ocr_json_path)

        if not os.path.exists(ocr_json_path):
            ocr_results, frames = obtain_ocr(src_image, self.text_executor)
            # convert CV frames to PIL frame
            frames = convert_frames(frames, img_format="pil")
            store_json_object(ocr_results, ocr_json_path)

        if "error" in ocr_results:
            return False, frames, [], [], ocr_results, file_hash

        if self.debug_visuals and self.debug_visuals_icr:
            visualize_icr(frames, ocr_results, file_hash)

        assert len(ocr_results) == len(frames)
        boxes = []
        words = []

        for k, (result, image) in enumerate(zip(ocr_results, frames)):
            if not isinstance(image, Image.Image):
                raise "Frame should have been an PIL.Image instance"
            boxes.append([])
            words.append([])

            for i, word in enumerate(result["words"]):
                words[k].append(word["text"])
                boxes[k].append(
                    normalize_bbox(word["box"], (image.size[0], image.size[1]))
                )
                # This is to prevent following error
                # The expanded size of the tensor (516) must match the existing size (512) at non-singleton dimension 1.
                if len(boxes[k]) == 512:
                    print("Clipping MAX boxes at 512")
                    break
            assert len(words[k]) == len(boxes[k])
        assert len(frames) == len(boxes) == len(words)
        return True, frames, boxes, words, ocr_results, file_hash

    def process(self, frames, boxes, words, file_hash):
        """process NER extraction"""

        annotations = []
        labels, id2label, label2id = self.get_label_info()

        for k, (_image, _boxes, _words) in enumerate(zip(frames, boxes, words)):
            if not isinstance(_image, Image.Image):
                raise "Frame should have been an PIL.Image instance"

            width = _image.size[0]
            height = _image.size[1]

            all_predictions, all_boxes, all_scores = self.inference(
                _image,
                _words,
                _boxes,
                labels,
                0.1,
            )

            true_predictions = all_predictions[0]
            true_boxes = all_boxes[0]
            true_scores = all_scores[0]

            # show detail scores
            if self.debug_scores:
                for i, val in enumerate(true_predictions):
                    tp = true_predictions[i]
                    score = true_scores[i]
                    print(f" >> {tp} : {score}")

            annotation = {
                "meta": {"imageSize": {"width": width, "height": height}, "page": k},
                "predictions": true_predictions,
                "boxes": true_boxes,
                "scores": true_scores,
            }
            annotations.append(annotation)

            if self.debug_visuals and self.debug_visuals_prediction:
                output_filename = f"/tmp/tensors/prediction_{file_hash}_{k}.png"
                visualize_prediction(
                    output_filename,
                    _image,
                    true_predictions,
                    true_boxes,
                    true_scores,
                    label2color=self.debug_colors,
                )

        annotation_json_path = os.path.join(
            __marie_home__, "annotation", f"{file_hash}.json"
        )
        ensure_exists(os.path.join(__marie_home__, "annotation"))
        store_json_object(annotations, annotation_json_path)

        return annotations

    # @requests()
    def extract(self, docs: Optional[DocumentArray] = None, **kwargs):
        """
        Args:
            docs : Documents to process, they will be none for now
        """

        queue_id: str = kwargs.get("queue_id", "0000-0000-0000-0000")
        checksum: str = kwargs.get("checksum", "0000-0000-0000-0000")
        image_src: str = kwargs.get("img_path", None)

        for key, value in kwargs.items():
            print("The value of {} is {}".format(key, value))

        loaded, frames, boxes, words, ocr_results, file_hash = self.preprocess(
            image_src
        )
        annotations = self.process(frames, boxes, words, file_hash)
        ner_results = self.postprocess(frames, annotations, ocr_results, file_hash)

        return ner_results
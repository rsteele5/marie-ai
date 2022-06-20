import math
import os
import time
import typing
from typing import Tuple, Any, List, Dict

from torchvision.transforms import Compose, InterpolationMode

from marie.lang import Object
from marie.logger import setup_logger
from marie.logging.predefined import default_logger
from marie.models.unilm.trocr.task import SROIETextRecognitionTask

import numpy as np
import torch
import torch.utils.data

from marie.document.icr_processor import IcrProcessor
from marie.models.icr.memory_dataset import MemoryDataset

import fairseq
from fairseq import utils
from fairseq_cli import generate
import torchvision.transforms as transforms

from marie.timer import Timer
from marie.utils.utils import batchify
from marie import __model_path__

device = "cuda" if torch.cuda.is_available() else "cpu"
# device = "cpu"

logger = default_logger


@Timer(text="init in {:.4f} seconds")
def init(model_path, beam=5) -> Tuple[Any, Any, Any, Any, Any, Compose, str]:
    # Currently, there is no support for mix precision(fp16) evaluation on CPU
    # https://github.com/pytorch/pytorch/issues/23377
    fp16 = True
    if device == "cpu":
        fp16 = False

    model, cfg, inference_task = fairseq.checkpoint_utils.load_model_ensemble_and_task(
        [model_path], arg_overrides={"beam": beam, "task": "text_recognition", "data": "", "fp16": fp16}
    )

    model[0].eval()

    # https://github.com/pytorch/pytorch/issues/23377
    if fp16:
        model[0].half().to(device)
    else:
        model[0].to(device)

    img_transform = transforms.Compose(
        [
            transforms.Resize((384, 384), interpolation=InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize(0.5, 0.5),
        ]
    )

    generator = inference_task.build_generator(
        model,
        cfg.generation,
        extra_gen_cls_kwargs={
            "lm_model": None,
            "lm_weight": None,
        },
    )

    bpe = inference_task.build_bpe(cfg.bpe)

    return model, cfg, inference_task, generator, bpe, img_transform, device


def preprocess_image(image, img_transform):
    im = image.convert("RGB").resize((384, 384))
    # this causes an error when batching due to the shape in deit.py
    # def forward(self, x):
    #     B, C, H, W = x.shape
    #

    # im = img_transform(im).unsqueeze(0).to(device).float()
    im = img_transform(im).to(device).float()
    return im


def preprocess_samples(src_images, img_transform):
    images = []
    for image in src_images:
        im = preprocess_image(image, img_transform)
        images.append(im)

    images = torch.stack(images, dim=0)
    sample = {
        "net_input": {"imgs": images},
    }

    return sample


# @Timer(text="Text in {:.4f} seconds")
def get_text(cfg, task, generator, model, samples, bpe):
    results = task.inference_step(generator, model, samples, prefix_tokens=None, constraints=None)
    predictions = []
    scores = []

    for i in range(len(results)):
        decoder_output = results[i][0]  # top1
        # TODO: how to interpret this ??
        score = decoder_output["score"]
        # print(f"score : {score}")

        hypo_tokens, hypo_str, alignment = utils.post_process_prediction(
            hypo_tokens=decoder_output["tokens"].int().cpu(),
            src_str="",
            alignment=decoder_output["alignment"],
            align_dict=None,
            tgt_dict=model[0].decoder.dictionary,
            remove_bpe=cfg.common_eval.post_process,
            extra_symbols_to_ignore=generate.get_symbols_to_strip_from_output(generator),
        )

        # TODO : fix the text scores
        detok_hypo_str = bpe.decode(hypo_str)
        predictions.append(detok_hypo_str)
        scores.append(0.9999)

    return predictions, scores


class TrOcrIcrProcessor(IcrProcessor):
    def __init__(
        self, work_dir: str = "/tmp/icr", models_dir: str = os.path.join(__model_path__, "trocr"), cuda: bool = True
    ) -> None:
        super().__init__(work_dir, cuda)
        pass

        model_path = os.path.join(models_dir, "trocr-large-printed.pt")
        logger.info(f"TROCR ICR processor [cuda={cuda}] : {model_path}")

        if not os.path.exists(model_path):
            raise Exception(f"File not found : {model_path}")

        start = time.time()
        beam = 5
        self.model, self.cfg, self.task, self.generator, self.bpe, self.img_transform, self.device = init(
            model_path, beam
        )
        logger.info("Model load elapsed: %s" % (time.time() - start))

        opt = Object()
        opt.rgb = False
        self.opt = opt

    def recognize_from_fragments(self, src_images, **kwargs) -> List[Dict[str, any]]:
        """Recognize text from image fragments synchronously.

        Args:
            src_images: A list of input images, supplied as numpy arrays with shape
                (H, W, 3).
        """

        logger.info("ICR processing : recognize_from_boxes via boxes")
        batch_size = 64
        size = len(src_images)
        total_batches = math.ceil(size / batch_size)

        try:
            opt = self.opt
            results = []
            start = time.time()

            for i, batch in enumerate(batchify(src_images, batch_size)):
                logger.debug(f"Processing batch [batch_idx, batch_size,] : {i}, {len(batch)}")
                images = batch

                eval_data = MemoryDataset(images=images, opt=opt)
                batch_start = time.time()

                images = [img for img, img_name in eval_data]
                samples = preprocess_samples(images, self.img_transform)
                predictions, scores = get_text(self.cfg, self.task, self.generator, self.model, samples, self.bpe)

                for k in range(len(predictions)):
                    pred = predictions[k]
                    score = scores[k]
                    _, img_name = eval_data[k]
                    text = pred
                    confidence = score
                    results.append({"confidence": confidence, "text": text, "id": img_name})
                logger.info("Batch time : %s" % (time.time() - batch_start))

            logger.info("ICR Time elapsed: %s" % (time.time() - start))

        except Exception as ex:
            raise ex
        return results

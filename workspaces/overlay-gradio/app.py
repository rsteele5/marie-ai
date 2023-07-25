import os

import gradio as gr
from PIL import Image

from marie.overlay.overlay import OverlayProcessor
from marie.utils.docs import frames_from_file
from marie.utils.utils import ensure_exists

overlay_processor = OverlayProcessor(work_dir=ensure_exists("/tmp/form-segmentation"))


def process_image(image):
    src_img_path = "/tmp/segment.png"
    image.save(src_img_path)
    docId = "segment"
    real, fake, blended = overlay_processor.segment(docId, src_img_path)

    return fake, blended


def interface():
    article = """
         # Document Overlay
        """

    def image_to_gallery(image_src):
        # image_file will be of tempfile._TemporaryFileWrapper type
        filename = image_src.name
        frames = frames_from_file(filename)

        return frames

    def gallery_click_handler(src_gallery, evt: gr.SelectData):
        selection = src_gallery[evt.index]
        filename = selection["name"]
        docId = "segment"
        frame = frames_from_file(filename)[0]

        real, fake, blended = overlay_processor.segment(docId, filename)
        return fake, blended

    with gr.Blocks() as iface:
        gr.Markdown(article)

        with gr.Row(variant="compact"):
            srcXXX = gr.components.Image(
                type="pil", source="upload", image_mode="L", label="Single page image"
            )
            src = gr.components.File(
                type="file", source="upload", label="Multi-page TIFF/PDF file"
            )

        with gr.Row():
            btn_reset = gr.Button("Clear")
            btn_submit = gr.Button("Process", variant="primary")
            btn_grid = gr.Button("Image-Grid", variant="primary")

        with gr.Row(live=True):
            gallery = gr.Gallery(
                label="Image frames",
                show_label=False,
                elem_id="gallery",
                interactive=True,
            ).style(columns=4, object_fit="contain", height="auto")

        with gr.Row():
            with gr.Column():
                fake = gr.components.Image(type="pil", label="fake")
            with gr.Column():
                blended = gr.components.Image(type="pil", label="blended")

        btn_grid.click(image_to_gallery, inputs=[src], outputs=gallery)
        btn_submit.click(process_image, inputs=[src], outputs=[fake, blended])
        btn_reset.click(lambda: src.reset())

        gallery.select(gallery_click_handler, inputs=[gallery], outputs=[fake, blended])

    iface.launch(
        debug=True,
        share=False,
        server_name="0.0.0.0",
    )


if __name__ == "__main__":
    import torch

    torch.set_float32_matmul_precision("high")
    torch.backends.cudnn.benchmark = False

    # print(torch._dynamo.list_backends())
    interface()

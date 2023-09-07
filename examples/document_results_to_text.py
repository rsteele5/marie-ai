import os
import threading
from pathlib import Path

from marie.utils.json import load_json_file
from marie.utils.utils import ensure_exists


def process_extract(
    queue_id: str, mode: str, file_location: str, stop_event: threading.Event = None
) -> str:
    if not os.path.exists(file_location):
        raise Exception(f"File not found : {file_location}")


def process_dir(src_dir: str, output_dir: str):
    root_asset_dir = os.path.expanduser(src_dir)
    output_path = os.path.expanduser(output_dir)

    for file_path in Path(root_asset_dir).rglob("*"):
        if not file_path.is_file():
            continue
        try:
            print(file_path)

            resolved_output_path = os.path.join(
                output_path, file_path.relative_to(root_asset_dir)
            )
            output_dir = os.path.dirname(resolved_output_path)
            filename = os.path.basename(resolved_output_path)
            name = os.path.splitext(filename)[0]
            os.makedirs(output_dir, exist_ok=True)

            results = load_json_file(file_path)
            lines = results[0]["lines"]
            lines = sorted(lines, key=lambda k: k['line'])
            text_output_path = os.path.join(output_dir, f"{name}.txt")
            with open(text_output_path, "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(line["text"] + "\n")

        except Exception as e:
            print(e)


if __name__ == "__main__":
    ensure_exists("/tmp/marie/results-text")
    # Specify the path to the file you would like to process
    process_dir("/tmp/marie/results", "/tmp/marie/results-text")

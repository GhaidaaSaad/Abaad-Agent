import os
import json
import uuid
import zipfile
from typing import Dict, Any

OUTPUTS_DIR = os.path.join(os.getcwd(), "outputs")


def ensure_job_dir(state: Dict[str, Any]) -> str:
    if "job_id" not in state:
        state["job_id"] = uuid.uuid4().hex[:8]
    job_dir = os.path.join(OUTPUTS_DIR, state["job_id"])
    os.makedirs(job_dir, exist_ok=True)
    return job_dir


def save_image_bytes(job_dir: str, data: bytes, filename: str = "image.png") -> str:
    path = os.path.join(job_dir, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path


def save_audio_bytes(job_dir: str, data: bytes, filename: str = "audio.wav") -> str:
    path = os.path.join(job_dir, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path


def save_text(job_dir: str, text: str, filename: str = "scene.txt") -> str:
    path = os.path.join(job_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def write_json(job_dir: str, obj: Dict[str, Any], filename: str = "metadata.json") -> str:
    path = os.path.join(job_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    return path


def make_zip(job_dir: str) -> str:
    zip_path = os.path.join(job_dir, "bundle.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(job_dir):
            for name in files:
                if name == "bundle.zip":
                    continue
                full = os.path.join(root, name)
                arc = os.path.relpath(full, job_dir)
                zf.write(full, arcname=arc)
    return zip_path



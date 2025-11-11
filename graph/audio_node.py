import os
import base64
from typing import Dict, Any, Optional
from loguru import logger
import requests
import numpy as np
import soundfile as sf

from utils.file_manager import ensure_job_dir, save_audio_bytes


def _generate_audio_hf_inference(prompt: str) -> Optional[bytes]:
    try:
        hf_token = os.getenv("HF_TOKEN")
        repo = os.getenv("MUSICGEN_MODEL_ID", "facebook/musicgen-small")
        if not hf_token:
            return None
        url = f"https://api-inference.huggingface.co/models/{repo}"
        headers = {"Authorization": f"Bearer {hf_token}"}
        payload = {"inputs": prompt}
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        # HF returns audio bytes directly or JSON error
        if resp.headers.get("content-type", "").startswith("audio/"):
            return resp.content
        # Some models return JSON with b64
        try:
            data = resp.json()
            b64 = data.get("audio", {}).get("data")
            if b64:
                return base64.b64decode(b64)
        except Exception:
            pass
        return None
    except Exception as e:
        logger.warning(f"HF Inference audio failed: {e}")
        return None


def _generate_placeholder_audio(prompt: str) -> bytes:
    sr = 32000
    duration = 6  # seconds, short placeholder
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Simple evolving tone
    freq = 220 + 20 * np.sin(2 * np.pi * 0.2 * t)
    audio = 0.1 * np.sin(2 * np.pi * freq * t).astype(np.float32)
    import io
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    return buf.getvalue()


def audio_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("audio_node: generating audio")
    job_dir = ensure_job_dir(state)
    prompt = state.get("sub_prompts", {}).get("audio") or state.get("prompt", "")

    audio_bytes = _generate_audio_hf_inference(prompt)
    if audio_bytes is None:
        audio_bytes = _generate_placeholder_audio(prompt)

    audio_path = save_audio_bytes(job_dir, audio_bytes, filename="audio.wav")
    state.setdefault("outputs", {})["audio_path"] = audio_path
    return state



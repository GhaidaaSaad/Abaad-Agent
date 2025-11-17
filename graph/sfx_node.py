import os
from typing import Dict, Any, List, Optional
from loguru import logger
import requests
import numpy as np
import soundfile as sf
import io

from utils.file_manager import ensure_job_dir, save_audio_bytes


def _generate_placeholder_sfx(prompt: str, index: int) -> bytes:
    """Generate a short placeholder sound effect as a WAV."""
    sample_rate = 44100
    duration = 2.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    freq = 440 + (index * 60)
    sfx_signal = 0.4 * np.sin(2 * np.pi * freq * t) * np.exp(-3 * t)
    buffer = io.BytesIO()
    sf.write(buffer, sfx_signal.astype(np.float32), sample_rate, format="WAV")
    return buffer.getvalue()


def _generate_sfx_elevenlabs(prompt: str) -> Optional[bytes]:
    """Generate sound effect using ElevenLabs API."""
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.debug("ELEVENLABS_API_KEY not set, skipping ElevenLabs SFX generation")
            return None
        
        logger.debug(f"Requesting SFX from ElevenLabs: {prompt[:50]}...")
        
        response = requests.post(
            "https://api.elevenlabs.io/v1/sound-generation",
            headers={"xi-api-key": api_key},
            json={
                "text": prompt,
                "duration_seconds": 2.0
            },
            timeout=60
        )
        response.raise_for_status()
        
        logger.debug(f"ElevenLabs SFX generated successfully ({len(response.content)} bytes)")
        return response.content
        
    except requests.RequestException as e:
        logger.warning(f"ElevenLabs API request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_data = e.response.json()
                logger.debug(f"ElevenLabs error response: {error_data}")
            except Exception:
                logger.debug(f"ElevenLabs error response (raw): {e.response.text}")
        return None
    except Exception as e:
        logger.warning(f"ElevenLabs SFX generation failed: {e}")
        return None


def _generate_single_sfx(prompt: str, index: int) -> bytes:
    """Generate a single SFX, with fallback to placeholder."""
    sfx_bytes = _generate_sfx_elevenlabs(prompt)
    if sfx_bytes is None:
        logger.debug(f"Using placeholder SFX for prompt {index + 1}")
        sfx_bytes = _generate_placeholder_sfx(prompt, index)
    return sfx_bytes


def sfx_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("sfx_node: generating sound effects")
    job_dir = ensure_job_dir(state)
    required_assets = state.get("required_assets", {}) or {}
    qty = required_assets.get("sfx", 0)
    if qty <= 0:
        logger.debug("No SFX requested; skipping node")
        return state

    analyze_outputs = state.get("sub_prompts", {})
    prompt_list = analyze_outputs.get("sfx") or []

    if not isinstance(prompt_list, list) or not prompt_list:
        base_prompt = state.get("prompt", "game world")
        prompt_list = [f"Sound effect #{i+1} for {base_prompt}" for i in range(qty)]

    paths: List[str] = []
    for idx in range(qty):
        prompt = prompt_list[idx] if idx < len(prompt_list) else prompt_list[-1]
        sfx_bytes = _generate_single_sfx(prompt, idx)
        filename = f"sfx_{idx + 1:02d}.wav"
        path = save_audio_bytes(job_dir, sfx_bytes, filename=filename)
        paths.append(path)

    state.setdefault("outputs", {})["sfx"] = paths
    state.setdefault("metadata", {}).setdefault("sfx_prompts", prompt_list)
    return state

import os
from typing import Dict, Any, Optional
from loguru import logger
import requests
import replicate
import numpy as np
import soundfile as sf

from utils.file_manager import ensure_job_dir, save_audio_bytes


def _generate_audio_replicate(prompt: str) -> Optional[bytes]:
    try:
        token = os.getenv("REPLICATE_API_TOKEN")
        if not token:
            raise RuntimeError("REPLICATE_API_TOKEN not set")
        
        # Set the API token for replicate client
        os.environ["REPLICATE_API_TOKEN"] = token
        
        # Extract theme/mood from prompt for music description
        music_prompt = f"ambient music for {prompt}"
        
        output = replicate.run(
            "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            input={
                "prompt": music_prompt,
                "duration": 10
            }
        )
        
        # Handle different output formats
        if hasattr(output, 'read'):
            # FileOutput object - read directly
            logger.debug("Reading audio from FileOutput object")
            audio_bytes = output.read()
            logger.debug("Audio generated successfully via Replicate MusicGen")
            return audio_bytes
        elif isinstance(output, str):
            # String URL
            audio_url = output
        elif isinstance(output, (list, tuple)) and len(output) > 0:
            # List of URLs
            audio_url = output[0]
        else:
            raise RuntimeError(f"Unexpected output format from Replicate: {type(output)}")
        
        # Download audio from URL
        audio_response = requests.get(audio_url, timeout=120)
        audio_response.raise_for_status()
        logger.debug("Audio generated successfully via Replicate MusicGen")
        return audio_response.content
        
    except Exception as e:
        logger.warning(f"Replicate audio generation failed: {e}")
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
    logger.info("audio_node: generating music and ambient audio")
    job_dir = ensure_job_dir(state)
    sub_prompts = state.get("sub_prompts", {}) or {}
    required_assets = state.get("required_assets", {}) or {}

    music_prompts = sub_prompts.get("audio_music") or []
    ambient_prompts = sub_prompts.get("audio_ambient") or []

    music_count = required_assets.get("music", 0)
    ambient_count = required_assets.get("ambient", 0)
    if music_count > 0:
        music_prompts = music_prompts[:music_count]
    if ambient_count > 0:
        ambient_prompts = ambient_prompts[:ambient_count]
    
    if not music_prompts and not ambient_prompts:
        logger.debug("No music or ambient requested; skipping")
        return state

    outputs = state.setdefault("outputs", {})
    music_paths = []
    ambient_paths = []

    def _generate_and_save(prompt_text: str, filename: str) -> str:
        audio_bytes = _generate_audio_replicate(prompt_text)
        if audio_bytes is None:
            audio_bytes = _generate_placeholder_audio(prompt_text)
        return save_audio_bytes(job_dir, audio_bytes, filename=filename)

    for idx, prompt in enumerate(music_prompts):
        logger.debug(f"Generating music track {idx + 1}/{len(music_prompts)}")
        filename = f"music_{idx + 1:02d}.wav"
        music_paths.append(_generate_and_save(prompt, filename))

    for idx, prompt in enumerate(ambient_prompts):
        logger.debug(f"Generating ambient loop {idx + 1}/{len(ambient_prompts)}")
        filename = f"ambient_{idx + 1:02d}.wav"
        ambient_paths.append(_generate_and_save(prompt, filename))

    # Fallback if no specific prompts available
    if not music_paths and not ambient_paths:
        base_prompt = sub_prompts.get("audio") or state.get("prompt", "")
        logger.debug("No targeted audio prompts provided; generating default track")
        music_paths.append(_generate_and_save(base_prompt, "music_01.wav"))

    if music_paths:
        outputs["audio_music"] = music_paths
        outputs["audio_path"] = music_paths[0]
    if ambient_paths:
        outputs["audio_ambient"] = ambient_paths
        if "audio_path" not in outputs:
            outputs["audio_path"] = ambient_paths[0]

    return state
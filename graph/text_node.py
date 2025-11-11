import os
from typing import Dict, Any
from loguru import logger
from openai import OpenAI

from utils.file_manager import ensure_job_dir, save_text


def _generate_text_openai(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_TEXT_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Write a vivid but concise narrative scene (120-200 words)."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )
    return completion.choices[0].message.content.strip()


def text_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("text_node: generating text")
    job_dir = ensure_job_dir(state)
    prompt = state.get("sub_prompts", {}).get("text") or state.get("prompt", "")

    try:
        text = _generate_text_openai(prompt)
        logger.debug("Text generated via OpenAI")
    except Exception as e:
        logger.warning(f"OpenAI text generation unavailable, using template: {e}")
        theme = state.get("theme", {})
        text = (
            f"In the heart of {theme.get('theme','the world')}, a traveler steps beneath glowing boughs. "
            f"The mood is {theme.get('mood','calm')}, the style {theme.get('style','soft and atmospheric')}. "
            f"Colors ripple like {', '.join(theme.get('color_palette', ['#00FFCC']))}. "
            f"{prompt}"
        )

    text_path = save_text(job_dir, text, filename="scene.txt")
    state.setdefault("outputs", {})["text_path"] = text_path
    return state



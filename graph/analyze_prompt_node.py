import os
import json
from dotenv import load_dotenv
from typing import Dict, Any
from loguru import logger
from openai import OpenAI

from utils.theme_parser import heuristic_theme_extract

load_dotenv()

SYSTEM_PROMPT = (
    "You are a game art director. Extract a unified theme from the user's idea. "
    "Return strict JSON with keys: theme, mood, style, color_palette (array of 3-5 hex color strings), "
    "and sub_prompts with keys image, audio, text, each a short prompt using identical theme keywords."
)


def _call_openai_for_theme(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )
    content = completion.choices[0].message.content
    try:
        return json.loads(content)
    except Exception:
        # try to extract JSON substring
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and start < end:
            return json.loads(content[start : end + 1])
        raise


def analyze_prompt_node(state: Dict[str, Any]) -> Dict[str, Any]:
    user_prompt = state.get("prompt", "")
    logger.info("analyze_prompt_node: extracting theme and sub-prompts")
    try:
        data = _call_openai_for_theme(user_prompt)
        logger.debug("Theme extracted via OpenAI")
    except Exception as e:
        logger.warning(f"OpenAI unavailable, using heuristic extractor: {e}")
        data = heuristic_theme_extract(user_prompt)

    state["theme"] = {
        "theme": data.get("theme"),
        "mood": data.get("mood"),
        "style": data.get("style"),
        "color_palette": data.get("color_palette"),
    }
    sub_prompts = data.get("sub_prompts") or {}
    if not sub_prompts:
        # Heuristic sub-prompts
        theme = state["theme"]
        keywords = f"{theme['theme']}, {theme['mood']}, {theme['style']}, palette {', '.join(theme['color_palette'])}"
        sub_prompts = {
            "image": f"Concept art of {keywords}.",
            "audio": f"30-second ambient loop for {keywords}.",
            "text": f"A short scene description featuring {keywords}.",
        }
    state["sub_prompts"] = sub_prompts
    return state



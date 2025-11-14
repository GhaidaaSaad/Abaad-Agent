import os
from typing import Dict, Any, List
from loguru import logger
from openai import OpenAI

from utils.file_manager import ensure_job_dir, save_text


SYSTEM_MESSAGES = {
    "scene": "Write a vivid but concise narrative scene (120-200 words).",
    "dialogue": "Write a short in-world dialogue exchange (4-6 lines).",
    "lore": "Write a lore entry or codex page (150-220 words).",
}


def _generate_text_openai(prompt: str, mode: str = "scene") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_TEXT_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    system_prompt = SYSTEM_MESSAGES.get(mode, SYSTEM_MESSAGES["scene"])
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )
    return completion.choices[0].message.content.strip()


def _fallback_text(prompt: str, theme: Dict[str, Any], mode: str) -> str:
    theme_name = theme.get("theme", "the world")
    mood = theme.get("mood", "calm")
    style = theme.get("style", "evocative")
    colors = ", ".join(theme.get("color_palette", []))

    if mode == "dialogue":
        return (
            f"[Scene: {theme_name} - mood {mood}, palette {colors}]\n"
            f"Hero: \"{prompt}\"\n"
            "Guide: \"Hold fast, the path ahead mirrors the colors around us.\""
        )
    if mode == "lore":
        return (
            f"{theme_name} Chronicle\n"
            f"Tone: {mood}\n"
            f"Style cues: {style}\n"
            f"{prompt}\n"
            "Legends whisper that the palette of the realm is woven into every artifact."
        )
    return (
        f"In {theme_name}, wrapped in {mood} moods and {style} flourishes, "
        f"tones of {colors} illuminate the path. {prompt}"
    )


def _generate_collection(
    prompts: List[str],
    mode: str,
    prefix: str,
    job_dir: str,
    theme: Dict[str, Any],
) -> List[str]:
    paths: List[str] = []
    for idx, prompt in enumerate(prompts):
        try:
            text = _generate_text_openai(prompt, mode=mode)
            logger.debug(f"Generated {mode} text #{idx + 1}")
        except Exception as exc:
            logger.warning(f"Text generation for {mode} #{idx + 1} failed, using template: {exc}")
            text = _fallback_text(prompt, theme, mode)
        filename = f"{prefix}_{idx + 1:02d}.txt"
        paths.append(save_text(job_dir, text, filename=filename))
    return paths


def text_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("text_node: generating text")
    job_dir = ensure_job_dir(state)
    sub_prompts = state.get("sub_prompts", {}) or {}
    theme = state.get("theme", {}) or {}

    description_prompts = sub_prompts.get("text_descriptions") or []
    dialogue_prompts = sub_prompts.get("text_dialogue") or []
    lore_prompts = sub_prompts.get("text_lore") or []

    if not description_prompts:
        fallback_prompt = sub_prompts.get("text") or state.get("prompt", "")
        if fallback_prompt:
            description_prompts = [fallback_prompt]

    outputs = state.setdefault("outputs", {})

    description_paths = _generate_collection(description_prompts, "scene", "description", job_dir, theme)
    dialogue_paths = _generate_collection(dialogue_prompts, "dialogue", "dialogue", job_dir, theme)
    lore_paths = _generate_collection(lore_prompts, "lore", "lore", job_dir, theme)

    if description_paths:
        outputs["text_descriptions"] = description_paths
        outputs["text_path"] = description_paths[0]
    elif not outputs.get("text_path"):
        # As a final fallback, create a minimal note
        minimal = _fallback_text("A brief scene overview.", theme, "scene")
        fallback_path = save_text(job_dir, minimal, filename="description_00.txt")
        outputs["text_path"] = fallback_path
        outputs["text_descriptions"] = [fallback_path]

    if dialogue_paths:
        outputs["text_dialogue"] = dialogue_paths
    if lore_paths:
        outputs["text_lore"] = lore_paths

    return state



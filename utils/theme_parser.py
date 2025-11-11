import re
from typing import Dict, Any, List


def _guess_palette(text: str) -> List[str]:
    text = text.lower()
    if "forest" in text or "green" in text:
        return ["#00FFCC", "#338833", "#223311"]
    if "desert" in text or "sand" in text:
        return ["#C2B280", "#D9A441", "#7A5C3A"]
    if "ocean" in text or "blue" in text:
        return ["#2E8BC0", "#145DA0", "#0C2D48"]
    if "neon" in text or "cyber" in text:
        return ["#00FFFF", "#FF00FF", "#101020"]
    return ["#A0A0A0", "#404040", "#202020"]


def _guess_theme(text: str) -> str:
    if "forest" in text.lower():
        return "Fantasy Forest"
    if "desert" in text.lower():
        return "Arid Desert"
    if "city" in text.lower() or "cyber" in text.lower():
        return "Neon City"
    return "Original World"


def _guess_mood(text: str) -> str:
    words = []
    for k in ["emotional", "calm", "gentle", "dark", "mysterious", "epic", "tense", "hopeful"]:
        if k in text.lower():
            words.append(k)
    return ", ".join(words) if words else "calm"


def _guess_style(text: str) -> str:
    candidates = []
    for k in ["soft light", "glowing", "pixel art", "painterly", "cinematic", "low poly"]:
        if k in text.lower():
            candidates.append(k)
    if "glow" in text.lower() and "glowing" not in candidates:
        candidates.append("glowing")
    return ", ".join(candidates) if candidates else "soft light"


def heuristic_theme_extract(user_prompt: str) -> Dict[str, Any]:
    theme = _guess_theme(user_prompt)
    mood = _guess_mood(user_prompt)
    style = _guess_style(user_prompt)
    palette = _guess_palette(user_prompt)
    keywords = f"{theme}, {mood}, {style}, palette {', '.join(palette)}"
    return {
        "theme": theme,
        "mood": mood,
        "style": style,
        "color_palette": palette,
        "sub_prompts": {
            "image": f"Concept art of {keywords}.",
            "audio": f"30-second ambient loop for {keywords}.",
            "text": f"A short scene description featuring {keywords}.",
        },
    }



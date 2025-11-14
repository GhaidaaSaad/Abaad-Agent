import re
from typing import Dict, Any, List, Optional


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


def _build_list(count: int, template: str) -> List[str]:
    return [template.format(index=i + 1) for i in range(max(0, count))]


def _extract_asset_counts(text: str) -> Dict[str, int]:
    """Extract asset counts from text using regex patterns."""
    text_lower = text.lower()
    counts = {
        "sprites_2d": 0,
        "textures": 0,
        "ui": 0,
        "models_3d": 0,
        "music": 0,
        "ambient": 0,
        "sfx": 0,
        "descriptions": 0,
        "dialogue": 0,
        "lore": 0,
    }
    
    # Patterns for sprites/characters
    sprite_patterns = [
        r"(\d+)\s*(?:character\s*)?(?:sprite|sprites|character|characters)",
        r"(?:need|want|require|requires)\s*(\d+)\s*(?:sprite|sprites|character|characters)",
        r"(\d+)\s*(?:2d\s*)?(?:sprite|sprites)",
    ]
    for pattern in sprite_patterns:
        match = re.search(pattern, text_lower)
        if match:
            counts["sprites_2d"] = max(counts["sprites_2d"], int(match.group(1)))
            break
    
    # Patterns for 3D models
    model_patterns = [
        r"(\d+)\s*(?:3d\s*)?(?:model|models|asset|assets)",
        r"(?:need|want|require|requires)\s*(\d+)\s*(?:3d\s*)?(?:model|models)",
        r"(\d+)\s*(?:castle|building|object|item)\s*(?:3d\s*)?(?:model|models)?",
    ]
    for pattern in model_patterns:
        match = re.search(pattern, text_lower)
        if match:
            counts["models_3d"] = max(counts["models_3d"], int(match.group(1)))
            break
    # Also check for single mentions without numbers
    if counts["models_3d"] == 0 and re.search(r"(?:3d\s*model|castle\s*3d|building\s*3d)", text_lower):
        counts["models_3d"] = 1
    
    # Patterns for SFX/sound effects
    sfx_patterns = [
        r"(\d+)\s*(?:combat\s*)?(?:sfx|sound\s*effect|sound\s*effects)",
        r"(?:need|want|require|requires)\s*(\d+)\s*(?:sfx|sound\s*effect|sound\s*effects)",
        r"(\d+)\s*(?:combat|action|game)\s*(?:sound|sfx)",
    ]
    for pattern in sfx_patterns:
        match = re.search(pattern, text_lower)
        if match:
            counts["sfx"] = max(counts["sfx"], int(match.group(1)))
            break
    
    # Patterns for music (with numbers)
    music_patterns_with_numbers = [
        r"(\d+)\s*(?:music|track|tracks|song|songs)",
        r"(?:need|want|require|requires)\s*(\d+)\s*(?:music|track|song)",
    ]
    for pattern in music_patterns_with_numbers:
        match = re.search(pattern, text_lower)
        if match:
            counts["music"] = max(counts["music"], int(match.group(1)))
            break
    # Check for single mentions without numbers
    if counts["music"] == 0 and re.search(r"(?:dungeon|background|ambient)\s*music", text_lower):
        counts["music"] = 1
    
    # Patterns for textures
    if re.search(r"(?:texture|textures|material|materials)", text_lower):
        match = re.search(r"(\d+)\s*(?:texture|textures|material|materials)", text_lower)
        counts["textures"] = int(match.group(1)) if match else 1
    
    # Patterns for UI
    if re.search(r"(?:ui|icon|icons|interface)", text_lower):
        match = re.search(r"(\d+)\s*(?:ui|icon|icons)", text_lower)
        counts["ui"] = int(match.group(1)) if match else 1
    
    # Defaults if nothing found but certain keywords present
    if counts["sprites_2d"] == 0 and re.search(r"(?:sprite|character|2d)", text_lower):
        counts["sprites_2d"] = 1
    if counts["sfx"] == 0 and re.search(r"(?:sfx|sound\s*effect)", text_lower):
        counts["sfx"] = 1
    
    return counts


def heuristic_theme_extract(user_prompt: str, preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    theme = _guess_theme(user_prompt)
    mood = _guess_mood(user_prompt)
    style = _guess_style(user_prompt)
    palette = _guess_palette(user_prompt)
    keywords = f"{theme}, {mood}, {style}, palette {', '.join(palette)}"
    
    # Extract asset counts from prompt text
    extracted_counts = _extract_asset_counts(user_prompt)
    
    preferences = preferences or {}
    assets = preferences.get("assets", {}) or {}
    audio = preferences.get("audio", {}) or {}
    text_pref = preferences.get("text", {}) or {}

    # Use extracted counts, fallback to preferences, then defaults
    if assets:
        sprites_count = max(extracted_counts["sprites_2d"], int(assets.get("sprites_2d", 0) or 0))
        textures_count = max(extracted_counts["textures"], int(assets.get("textures", 0) or 0))
        ui_count = max(extracted_counts["ui"], int(assets.get("ui", 0) or 0))
        models_count = max(extracted_counts["models_3d"], int(assets.get("models_3d", 0) or 0))
    else:
        sprites_count = extracted_counts["sprites_2d"] if extracted_counts["sprites_2d"] > 0 else 1
        textures_count = extracted_counts["textures"]
        ui_count = extracted_counts["ui"]
        models_count = extracted_counts["models_3d"]

    if audio:
        music_count = max(extracted_counts["music"], int(audio.get("music", 0) or 0))
        ambient_count = max(extracted_counts["ambient"], int(audio.get("ambient", 0) or 0))
        sfx_count = max(extracted_counts["sfx"], int(audio.get("sfx", 0) or 0))
    else:
        music_count = extracted_counts["music"] if extracted_counts["music"] > 0 else 1
        ambient_count = extracted_counts["ambient"]
        sfx_count = extracted_counts["sfx"]

    if text_pref:
        desc_count = max(extracted_counts["descriptions"], int(text_pref.get("descriptions", 0) or 0))
        dialogue_count = max(extracted_counts["dialogue"], int(text_pref.get("dialogue", 0) or 0))
        lore_count = max(extracted_counts["lore"], int(text_pref.get("lore", 0) or 0))
    else:
        desc_count = extracted_counts["descriptions"] if extracted_counts["descriptions"] > 0 else 1
        dialogue_count = extracted_counts["dialogue"]
        lore_count = extracted_counts["lore"]

    image_prompt = f"Concept art of {keywords}."
    audio_prompt = f"30-second ambient loop for {keywords}."
    text_prompt = f"A short scene description featuring {keywords}."

    return {
        "theme": theme,
        "mood": mood,
        "style": style,
        "color_palette": palette,
        "required_assets": {
            "sprites_2d": sprites_count,
            "textures": textures_count,
            "ui": ui_count,
            "models_3d": models_count,
            "music": music_count,
            "ambient": ambient_count,
            "sfx": sfx_count,
            "descriptions": desc_count,
            "dialogue": dialogue_count,
            "lore": lore_count,
        },
        "sub_prompts": {
            "image": image_prompt,
            "sprites_2d": _build_list(sprites_count, f"{image_prompt} Variant {{index}}"),
            "textures": _build_list(textures_count, f"Texture sheet {keywords} Variant {{index}}"),
            "ui": _build_list(ui_count, f"UI element set {keywords} Variant {{index}}"),
            "models_3d": _build_list(models_count, f"3D model {keywords} Asset {{index}}"),
            "audio": audio_prompt,
            "audio_music": _build_list(music_count, f"Background music track {keywords} #{{index}}"),
            "audio_ambient": _build_list(ambient_count, f"Ambient loop {keywords} #{{index}}"),
            "sfx": _build_list(sfx_count, f"Sound effect {keywords} #{{index}}"),
            "text": text_prompt,
            "text_descriptions": _build_list(desc_count, f"Narrative scene {keywords} #{{index}}"),
            "text_dialogue": _build_list(dialogue_count, f"Dialogue excerpt {keywords} #{{index}}"),
            "text_lore": _build_list(lore_count, f"Lore entry {keywords} #{{index}}"),
        },
    }



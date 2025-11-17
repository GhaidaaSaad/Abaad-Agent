import os
import json
from dotenv import load_dotenv
from typing import Dict, Any, List
from loguru import logger
from openai import OpenAI

from utils.theme_parser import heuristic_theme_extract

load_dotenv()

SYSTEM_PROMPT = (
    "You are Chief Art Director for a Unity game project. Analyze the user's game description and extract:\n"
    "1. Theme and Style Guide (mood, colors, art style, visual direction)\n"
    "2. Required assets (how many sprites? 3D models? audio types? text content?)\n"
    "3. Generate prompts for each asset following the Style Guide\n\n"
    "IMPORTANT: You MUST respond with valid JSON only. No markdown, no code blocks, no explanations.\n"
    "Return a JSON object with these exact keys:\n"
    "{\n"
    "  \"theme\": \"string (e.g., 'Dark Fantasy RPG')\",\n"
    "  \"mood\": \"string (e.g., 'dark, moody, gothic')\",\n"
    "  \"style\": \"string (e.g., 'hand-painted, atmospheric, low-poly')\",\n"
    "  \"color_palette\": [\"#HEX1\", \"#HEX2\", \"#HEX3\"],\n"
    "  \"style_guide\": \"string (comprehensive style description)\",\n"
    "  \"required_assets\": {\n"
    "    \"sprites_2d\": 0,\n"
    "    \"textures\": 0,\n"
    "    \"ui\": 0,\n"
    "    \"models_3d\": 0,\n"
    "    \"music\": 0,\n"
    "    \"ambient\": 0,\n"
    "    \"sfx\": 0,\n"
    "    \"descriptions\": 0,\n"
    "    \"dialogue\": 0,\n"
    "    \"lore\": 0\n"
    "  },\n"
    "  \"asset_prompts\": {\n"
    "    \"sprites_2d\": [\"prompt1\", \"prompt2\"],\n"
    "    \"textures\": [],\n"
    "    \"ui\": [],\n"
    "    \"models_3d\": [],\n"
    "    \"audio_music\": [],\n"
    "    \"audio_ambient\": [],\n"
    "    \"sfx\": [],\n"
    "    \"text_descriptions\": [],\n"
    "    \"text_dialogue\": [],\n"
    "    \"text_lore\": []\n"
    "  }\n"
    "}\n"
    "Ensure all prompts reuse the same core theme keywords and follow the style_guide for consistency."
)


def _call_openai_for_analysis(prompt: str) -> Dict[str, Any]:
    """Call OpenAI to extract requirements and generate asset prompts."""
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)
    user_message = (
        f"Game description:\n{prompt}\n\n"
        "Analyze this description and extract all requirements. "
        "Determine what assets are needed and generate appropriate prompts. "
        "Respond with valid JSON only, no markdown formatting."
    )
    try:
        completion = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},  # Force JSON mode
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
        )
        content = completion.choices[0].message.content
        logger.debug(f"OpenAI raw response (first 200 chars): {content[:200]}")
        
        # Try direct JSON parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Direct JSON parse failed: {e}")
            # Try to extract JSON substring (remove markdown code blocks if present)
            content_clean = content.strip()
            # Remove markdown code blocks
            if content_clean.startswith("```"):
                lines = content_clean.split("\n")
                content_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else content_clean
            if content_clean.startswith("```json"):
                lines = content_clean.split("\n")
                content_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else content_clean
            
            # Find JSON object boundaries
            start = content_clean.find("{")
            end = content_clean.rfind("}")
            if start != -1 and end != -1 and start < end:
                json_str = content_clean[start : end + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e2:
                    logger.error(f"Extracted JSON substring also invalid: {e2}")
                    logger.error(f"Extracted substring: {json_str[:500]}")
                    raise ValueError(f"Failed to parse JSON from OpenAI response: {e2}")
            else:
                raise ValueError(f"No JSON object found in response: {content[:500]}")
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise


def _coerce_list(value) -> List[str]:
    """Convert value to list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        val = value.strip()
        return [val] if val else []
    return [str(value)]


def _ensure_prompt_count(prompts: List[str], count: int, fallback_base: str) -> List[str]:
    """Ensure we have enough prompts, generating fallbacks if needed."""
    if count <= 0:
        return []
    if not prompts:
        prompts = []
    # Pad with variations
    while len(prompts) < count:
        if prompts:
            # Create variation of last prompt
            prompts.append(f"{prompts[-1]} (variation {len(prompts) + 1})")
        else:
            prompts.append(fallback_base)
    return prompts[:count]


def analyze_prompt_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze user prompt and extract all requirements automatically."""
    user_prompt = state.get("prompt", "")
    logger.info("analyze_prompt_node: extracting theme, style guide, and asset requirements")
    
    fallback = None
    try:
        data = _call_openai_for_analysis(user_prompt)
        logger.debug("Requirements extracted via OpenAI")
        # Try to get fallback for missing fields, but don't fail if it errors
        try:
            fallback = heuristic_theme_extract(user_prompt, {})
        except Exception as fallback_err:
            logger.debug(f"Fallback extraction failed (non-critical): {fallback_err}")
            fallback = {}
    except Exception as e:
        logger.warning(f"OpenAI unavailable, using heuristic extractor: {e}")
        try:
            data = heuristic_theme_extract(user_prompt, {})
            fallback = data
        except Exception as heuristic_err:
            logger.error(f"Heuristic extractor also failed: {heuristic_err}")
            # Create minimal fallback
            data = {
                "theme": "Game World",
                "mood": "atmospheric",
                "style": "stylized",
                "color_palette": ["#808080", "#404040", "#202020"],
                "required_assets": {"sprites_2d": 1, "music": 1, "descriptions": 1},
                "asset_prompts": {}
            }
            fallback = data

    # Extract theme and style guide
    state["theme"] = {
        "theme": data.get("theme") or fallback.get("theme", "Game World"),
        "mood": data.get("mood") or fallback.get("mood", "atmospheric"),
        "style": data.get("style") or fallback.get("style", "stylized"),
        "color_palette": data.get("color_palette") or fallback.get("color_palette", ["#808080", "#404040", "#202020"]),
    }
    state["style_guide"] = data.get("style_guide") or f"{state['theme']['theme']} style: {state['theme']['mood']}, {state['theme']['style']}"

    # Extract required assets (AI-determined counts)
    required_assets = data.get("required_assets") or {}
    # Use heuristic fallback if OpenAI didn't provide required_assets
    if not required_assets and fallback.get("required_assets"):
        required_assets = fallback.get("required_assets")
    if not required_assets:
        # Default fallback: generate at least one of each type mentioned
        required_assets = {
            "sprites_2d": 1,
            "textures": 0,
            "ui": 0,
            "models_3d": 0,
            "music": 1,
            "ambient": 0,
            "sfx": 0,
            "descriptions": 1,
            "dialogue": 0,
            "lore": 0,
        }
    state["required_assets"] = required_assets

    # Extract and normalize asset prompts
    asset_prompts_raw = data.get("asset_prompts") or {}
    fallback_prompts = fallback.get("sub_prompts") or {}
    
    # Build asset_prompts ensuring counts match required_assets
    asset_prompts = {}
    theme_keywords = f"{state['theme']['theme']}, {state['theme']['mood']}, {state['theme']['style']}"
    
    # Sprites
    sprites = _coerce_list(asset_prompts_raw.get("sprites_2d") or fallback_prompts.get("sprites_2d"))
    asset_prompts["sprites_2d"] = _ensure_prompt_count(
        sprites, 
        required_assets.get("sprites_2d", 0),
        f"2D sprite concept art of {theme_keywords}"
    )
    
    # Textures
    textures = _coerce_list(asset_prompts_raw.get("textures") or fallback_prompts.get("textures"))
    asset_prompts["textures"] = _ensure_prompt_count(
        textures,
        required_assets.get("textures", 0),
        f"Texture material for {theme_keywords}"
    )
    
    # UI
    ui = _coerce_list(asset_prompts_raw.get("ui") or fallback_prompts.get("ui"))
    asset_prompts["ui"] = _ensure_prompt_count(
        ui,
        required_assets.get("ui", 0),
        f"UI element icon for {theme_keywords}"
    )
    
    # 3D Models
    models = _coerce_list(asset_prompts_raw.get("models_3d") or fallback_prompts.get("models_3d"))
    asset_prompts["models_3d"] = _ensure_prompt_count(
        models,
        required_assets.get("models_3d", 0),
        f"3D model asset for {theme_keywords}"
    )
    
    # Music
    music = _coerce_list(asset_prompts_raw.get("audio_music") or fallback_prompts.get("audio_music"))
    asset_prompts["audio_music"] = _ensure_prompt_count(
        music,
        required_assets.get("music", 0),
        f"Background music for {theme_keywords}"
    )
    
    # Ambient
    ambient = _coerce_list(asset_prompts_raw.get("audio_ambient") or fallback_prompts.get("audio_ambient"))
    asset_prompts["audio_ambient"] = _ensure_prompt_count(
        ambient,
        required_assets.get("ambient", 0),
        f"Ambient sound loop for {theme_keywords}"
    )
    
    # SFX
    sfx = _coerce_list(asset_prompts_raw.get("sfx") or fallback_prompts.get("sfx"))
    asset_prompts["sfx"] = _ensure_prompt_count(
        sfx,
        required_assets.get("sfx", 0),
        f"Sound effect for {theme_keywords}"
    )
    
    # Text descriptions
    descriptions = _coerce_list(asset_prompts_raw.get("text_descriptions") or fallback_prompts.get("text_descriptions"))
    asset_prompts["text_descriptions"] = _ensure_prompt_count(
        descriptions,
        required_assets.get("descriptions", 0),
        f"World description for {theme_keywords}"
    )
    
    # Dialogue
    dialogue = _coerce_list(asset_prompts_raw.get("text_dialogue") or fallback_prompts.get("text_dialogue"))
    asset_prompts["text_dialogue"] = _ensure_prompt_count(
        dialogue,
        required_assets.get("dialogue", 0),
        f"Character dialogue for {theme_keywords}"
    )
    
    # Lore
    lore = _coerce_list(asset_prompts_raw.get("text_lore") or fallback_prompts.get("text_lore"))
    asset_prompts["text_lore"] = _ensure_prompt_count(
        lore,
        required_assets.get("lore", 0),
        f"Lore entry for {theme_keywords}"
    )
    
    # Legacy compatibility: primary strings
    asset_prompts["image"] = asset_prompts["sprites_2d"][0] if asset_prompts["sprites_2d"] else ""
    asset_prompts["audio"] = asset_prompts["audio_music"][0] if asset_prompts["audio_music"] else (asset_prompts["audio_ambient"][0] if asset_prompts["audio_ambient"] else "")
    asset_prompts["text"] = asset_prompts["text_descriptions"][0] if asset_prompts["text_descriptions"] else ""
    
    state["sub_prompts"] = asset_prompts
    logger.debug(f"Extracted {sum(len(v) for v in asset_prompts.values() if isinstance(v, list))} asset prompts")
    
    return state
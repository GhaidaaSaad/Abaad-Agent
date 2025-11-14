
from graph.analyze_prompt_node import analyze_prompt_node
from graph.image_node import image_node
from graph.audio_node import audio_node
from graph.sfx_node import sfx_node
from graph.text_node import text_node
from graph.model_3d_node import model_3d_node
from graph.packaging_node import packaging_node


def _wants_image_assets(required_assets: Dict[str, Any]) -> bool:
    """Check if any 2D image assets are required."""
    wanted_keys = {"sprites_2d", "textures", "ui"}
    return any(required_assets.get(key, 0) > 0 for key in wanted_keys)


def _wants_3d_assets(required_assets: Dict[str, Any]) -> bool:
    """Check if 3D models are required."""
    return required_assets.get("models_3d", 0) > 0


def _wants_music(required_assets: Dict[str, Any]) -> bool:
    """Check if music or ambient audio is required."""
    return required_assets.get("music", 0) > 0 or required_assets.get("ambient", 0) > 0


def _wants_sfx(required_assets: Dict[str, Any]) -> bool:
    """Check if sound effects are required."""
    return required_assets.get("sfx", 0) > 0


def _wants_text_assets(required_assets: Dict[str, Any]) -> bool:
    """Check if any text content is required."""
    text_keys = {"descriptions", "dialogue", "lore"}
    return any(required_assets.get(key, 0) > 0 for key in text_keys)


def build_workflow():
    """Build dynamic workflow based on AI-extracted requirements."""
    logger.debug("Building LangGraph workflow (will be determined by AI analysis)")
    
    # We can't know what assets are needed until analyze_prompt_node runs
    # So we build a full pipeline and nodes will skip if not needed
    graph = StateGraph(dict)

    graph.add_node("analyze_prompt", analyze_prompt_node)
    graph.add_node("image", image_node)
    graph.add_node("models_3d", model_3d_node)
    graph.add_node("audio", audio_node)
    graph.add_node("sfx", sfx_node)
    graph.add_node("text", text_node)
    graph.add_node("packaging", packaging_node)

    # Sequential pipeline: analyze first, then generate all assets, then package
    graph.set_entry_point("analyze_prompt")
    graph.add_edge("analyze_prompt", "image")
    graph.add_edge("image", "models_3d")
    graph.add_edge("models_3d", "audio")
    graph.add_edge("audio", "sfx")
    graph.add_edge("sfx", "text")
    graph.add_edge("text", "packaging")
    graph.add_edge("packaging", END)

    return graph.compile()

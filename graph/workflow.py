from typing import Dict, Any
from langgraph.graph import StateGraph, END
from loguru import logger

from graph.analyze_prompt_node import analyze_prompt_node
from graph.image_node import image_node
from graph.audio_node import audio_node
from graph.text_node import text_node
from graph.packaging_node import packaging_node


def _should_generate_image(state: Dict[str, Any]) -> bool:
    return True


def _should_generate_audio(state: Dict[str, Any]) -> bool:
    return True


def _should_generate_text(state: Dict[str, Any]) -> bool:
    return True


def build_workflow():
    logger.debug("Building LangGraph workflow")
    graph = StateGraph(dict)

    graph.add_node("analyze_prompt", analyze_prompt_node)
    graph.add_node("image", image_node)
    graph.add_node("audio", audio_node)
    graph.add_node("text", text_node)
    graph.add_node("packaging", packaging_node)

    graph.set_entry_point("analyze_prompt")

    # Sequential edges to avoid concurrent root-state writes
    graph.add_edge("analyze_prompt", "image")
    graph.add_edge("image", "audio")
    graph.add_edge("audio", "text")
    graph.add_edge("text", "packaging")

    graph.add_edge("packaging", END)

    return graph.compile()



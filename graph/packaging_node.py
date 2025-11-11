import json
from typing import Dict, Any
from loguru import logger

from utils.file_manager import ensure_job_dir, write_json, make_zip


def packaging_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("packaging_node: writing metadata and zipping outputs")
    job_dir = ensure_job_dir(state)
    outputs = state.get("outputs", {})
    metadata = {
        "prompt": state.get("prompt"),
        "theme": state.get("theme"),
        "sub_prompts": state.get("sub_prompts"),
        "outputs": outputs,
    }
    write_json(job_dir, metadata, filename="metadata.json")
    zip_path = make_zip(job_dir)
    state["zip_path"] = zip_path
    return state



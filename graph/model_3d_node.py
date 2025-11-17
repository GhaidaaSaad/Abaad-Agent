import os
import time
from typing import Dict, Any, List, Optional
from loguru import logger
import requests

from utils.file_manager import ensure_job_dir, save_text

TRIPO3D_BASE_URL = "https://api.tripo3d.ai/v2/openapi"


def _generate_placeholder_glb(prompt: str, index: int) -> bytes:
    """Return a simple placeholder GLB content (fake binary)."""
    message = (
        f"Placeholder GLB for prompt #{index + 1}\n"
        f"Description: {prompt}\n"
        "Replace with real Tripo3D output."
    )
    return message.encode("utf-8")


def _create_tripo3d_task(api_key: str, prompt: str) -> str:
    """Create Tripo3D task with correct endpoint."""
    try:
        url = f"{TRIPO3D_BASE_URL}/task"
        logger.debug(f"Creating Tripo3D task for: {prompt[:50]}...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "type": "text_to_model",
            "prompt": prompt
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logger.debug(f"Tripo3D task creation response: {result}")
        
        task_id = result.get("data", {}).get("task_id")
        
        if not task_id:
            # Try alternative locations
            task_id = (
                result.get("task_id") or 
                result.get("id") or
                result.get("data", {}).get("id")
            )
        
        if not task_id:
            raise RuntimeError(f"No task_id in response: {result}")
        
        logger.info(f"Tripo3D task created: {task_id}")
        return task_id
        
    except Exception as e:
        logger.error(f"Failed to create Tripo3D task: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_data = e.response.json()
                logger.error(f"Tripo3D task creation error response: {error_data}")
            except Exception:
                logger.error(f"Tripo3D task creation error response (raw): {e.response.text}")
        raise


def _poll_tripo3d_task(api_key: str, task_id: str, max_wait: int = 600) -> dict:
    """Poll task status until completed, return task data with model URL."""
    try:
        poll_interval = 5  # seconds
        elapsed = 0
        
        logger.debug(f"Polling Tripo3D task {task_id} status...")
        
        while elapsed < max_wait:
            # Poll using GET endpoint with task_id
            url = f"{TRIPO3D_BASE_URL}/task/{task_id}"
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Tripo3D task query response: {result}")
            
            # Extract task data and status (handle different response structures)
            task_data = result.get("data", result)
            status = (
                task_data.get("status") or 
                result.get("status") or 
                task_data.get("state") or
                task_data.get("task_status")
            )
            
            logger.debug(f"Task {task_id} status: {status} (elapsed: {elapsed}s)")
            
            if status in ("completed", "success", "done", "SUCCESS", "COMPLETED"):
                logger.info(f"Tripo3D task {task_id} completed successfully")
                return task_data
            
            elif status in ("failed", "error", "FAILED", "ERROR"):
                error_msg = (
                    task_data.get("error") or 
                    task_data.get("message") or 
                    result.get("error") or
                    result.get("message") or
                    "Unknown error"
                )
                raise RuntimeError(f"Task failed: {error_msg}")
            
            elif status in ("pending", "processing", "in_progress", "running", "queued", 
                           "PENDING", "PROCESSING", "RUNNING", "QUEUED"):
                time.sleep(poll_interval)
                elapsed += poll_interval
            else:
                logger.warning(f"Unknown status '{status}', continuing to poll...")
                time.sleep(poll_interval)
                elapsed += poll_interval
        
        raise TimeoutError(f"Tripo3D task {task_id} did not complete within {max_wait} seconds")
        
    except Exception as e:
        logger.error(f"Failed to poll Tripo3D task: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_data = e.response.json()
                logger.error(f"Tripo3D task query error response: {error_data}")
            except Exception:
                logger.error(f"Tripo3D task query error response (raw): {e.response.text}")
        raise


def _download_tripo3d_model(task_data: dict) -> bytes:
    """Download GLB model from task result."""
    try:
        # Extract model URL from task data
        # Tripo3D API returns the URL in multiple possible locations:
        # 1. task_data['result']['pbr_model']['url'] (preferred, structured)
        # 2. task_data['output']['pbr_model'] (direct URL string)
        # 3. Fallback to other common locations
        model_url = None
        
        # Check result.pbr_model.url (structured format)
        if task_data.get("result", {}).get("pbr_model", {}).get("url"):
            model_url = task_data["result"]["pbr_model"]["url"]
        # Check output.pbr_model (direct URL string)
        elif task_data.get("output", {}).get("pbr_model"):
            model_url = task_data["output"]["pbr_model"]
        # Fallback to other common locations
        else:
            model_url = (
                task_data.get("model_url") or 
                task_data.get("url") or 
                task_data.get("download_url") or
                task_data.get("glb_url") or
                task_data.get("result", {}).get("model_url") or
                task_data.get("result", {}).get("url") or
                task_data.get("result", {}).get("glb_url") or
                task_data.get("output", {}).get("url") or
                task_data.get("output", {}).get("model_url") or
                task_data.get("output", {}).get("glb_url") or
                task_data.get("data", {}).get("model_url") or
                task_data.get("data", {}).get("url") or
                task_data.get("data", {}).get("glb_url")
            )
        
        if not model_url:
            logger.error(f"Task data structure: {task_data}")
            raise RuntimeError(f"No model_url/glb_url found in task data. Available keys: {list(task_data.keys())}")
        
        logger.info(f"Downloading Tripo3D model from: {model_url}")
        
        # Download with streaming for large files
        response = requests.get(model_url, stream=True, timeout=180)
        response.raise_for_status()
        
        # Read content in chunks for efficient memory usage
        content = b""
        chunk_size = 8192  # 8KB chunks
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                content += chunk
        
        logger.info(f"Downloaded Tripo3D GLB model: {len(content)} bytes")
        return content
        
    except Exception as e:
        logger.error(f"Failed to download Tripo3D model: {e}")
        raise


def _generate_3d_model_tripo3d(prompt: str) -> Optional[bytes]:
    """Generate 3D model using Tripo3D API."""
    api_key = os.getenv("TRIPO3D_API_KEY")
    if not api_key:
        raise RuntimeError("TRIPO3D_API_KEY must be set in environment")
    
    try:
        # Step 1: Create task
        task_id = _create_tripo3d_task(api_key, prompt)
        
        # Step 2: Poll until completed (max 10 minutes)
        task_data = _poll_tripo3d_task(api_key, task_id, max_wait=600)
        
        # Step 3: Download GLB
        glb_bytes = _download_tripo3d_model(task_data)
        
        logger.info("Tripo3D 3D model generated successfully")
        return glb_bytes
        
    except requests.RequestException as e:
        logger.error(f"Tripo3D API request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_data = e.response.json()
                logger.error(f"Tripo3D API error response: {error_data}")
            except Exception:
                logger.error(f"Tripo3D API error response (raw): {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Tripo3D generation failed: {e}")
        raise


def _generate_single_model(prompt: str, index: int) -> bytes:
    """Generate a single 3D model, with fallback to placeholder."""
    try:
        return _generate_3d_model_tripo3d(prompt)
    except Exception as exc:
        logger.warning(
            f"Tripo3D generation failed (model {index + 1}), using placeholder: {exc}"
        )
        return _generate_placeholder_glb(prompt, index)


def _save_glb(job_dir: str, data: bytes, filename: str) -> str:
    """Save GLB file to job directory."""
    path = os.path.join(job_dir, filename)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def model_3d_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate 3D models based on AI-extracted requirements."""
    logger.info("model_3d_node: generating 3D models")
    job_dir = ensure_job_dir(state)
    required_assets = state.get("required_assets", {}) or {}
    qty = required_assets.get("models_3d", 0)
    if qty <= 0:
        logger.debug("No 3D models requested; skipping node")
        return state

    prompts: List[str] = []
    analyze_outputs = state.get("sub_prompts", {})
    model_prompts = analyze_outputs.get("models_3d")
    if isinstance(model_prompts, list):
        prompts = model_prompts
    if not prompts:
        base_prompt = state.get("prompt", "Original game world")
        prompts = [f"3D asset #{i+1} for {base_prompt}" for i in range(qty)]

    outputs = []
    for idx in range(qty):
        prompt = prompts[idx] if idx < len(prompts) else prompts[-1]
        logger.info(f"Generating 3D model {idx + 1}/{qty}: {prompt[:50]}...")
        glb_bytes = _generate_single_model(prompt, idx)
        filename = f"model_{idx + 1:02d}.glb"
        glb_path = _save_glb(job_dir, glb_bytes, filename)
        outputs.append(glb_path)
        logger.debug(f"Saved 3D model to: {glb_path}")

    state.setdefault("outputs", {})["models_3d"] = outputs
    meta = {
        "model_prompts": prompts,
        "count": qty,
    }
    save_text(job_dir, str(meta), filename="models_meta.txt")
    return state

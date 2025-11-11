import os
import requests
from typing import Dict, Any, Optional
from loguru import logger
from openai import OpenAI

from utils.file_manager import ensure_job_dir, save_image_bytes


def _generate_image_with_diffusers(prompt: str) -> Optional[bytes]:
	try:
		api_key = os.getenv("OPENAI_API_KEY")
		if not api_key:
			raise RuntimeError("OPENAI_API_KEY not set")
		client = OpenAI(api_key=api_key)
		resp = client.images.generate(
			model="dall-e-3",
			prompt=prompt,
			size="1024x1024",
			quality="standard",
			n=1,
		)
		url = resp.data[0].url
		if not url:
			raise RuntimeError("No image URL returned from OpenAI")
		# Retry with exponential backoff and increased timeout
		timeout_s = 300
		max_attempts = 4
		last_err: Optional[Exception] = None
		for attempt in range(1, max_attempts + 1):
			try:
				r = requests.get(url, timeout=timeout_s)
				r.raise_for_status()
				logger.debug("Image generated successfully via DALL·E 3")
				return r.content
			except Exception as e:
				last_err = e
				if attempt < max_attempts:
					backoff = 2 ** (attempt - 1)
					logger.warning(f"DALL·E image download failed (attempt {attempt}/{max_attempts}), retrying in {backoff}s: {e}")
					import time
					time.sleep(backoff)
				else:
					raise last_err
	except Exception as e:
		logger.warning(f"DALL·E 3 generation failed or unavailable: {e}")
		return None


def _generate_placeholder_image(prompt: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    img = Image.new("RGB", (768, 512), color=(34, 51, 34))
    draw = ImageDraw.Draw(img)
    text = (prompt[:120] + "...") if len(prompt) > 120 else prompt
    draw.text((20, 20), "Placeholder Image", fill=(0, 255, 204))
    draw.text((20, 60), text, fill=(255, 255, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def image_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("image_node: generating image")
    job_dir = ensure_job_dir(state)
    prompt = state.get("sub_prompts", {}).get("image") or state.get("prompt", "")

    img_bytes = _generate_image_with_diffusers(prompt)
    if img_bytes is None:
        img_bytes = _generate_placeholder_image(prompt)

    img_path = save_image_bytes(job_dir, img_bytes, filename="image.png")
    state.setdefault("outputs", {})["image_path"] = img_path
    return state



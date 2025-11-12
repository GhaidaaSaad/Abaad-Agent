import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger

from graph.workflow import build_workflow


load_dotenv()
app = FastAPI(title="ABAAD-Agent API", version="0.1.0")
_workflow = build_workflow()


class GenerateRequest(BaseModel):
    prompt: str


@app.post("/generate")
async def generate(req: GenerateRequest):
    try:
        # Validate prompt
        prompt = req.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        if len(prompt) < 10:
            raise HTTPException(
                status_code=400, detail="Prompt must be at least 10 characters long"
            )
        
        state = {"prompt": prompt}
        result = _workflow.invoke(state)
        zip_path = result.get("zip_path")
        if not zip_path or not os.path.exists(zip_path):
            raise HTTPException(status_code=500, detail="Failed to package outputs")
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=os.path.basename(zip_path),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Generation failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


# To run: uvicorn api.app:app --host 0.0.0.0 --port 8000
# 🎮 ABAAD-Agent

AI agent that generates multi-modal game assets (images,3d Models, audio, text) from a single prompt using LangGraph.

---

## 🚀 Quick Start

### 1. Get API Keys

Sign up at [OpenAI](https://platform.openai.com/api-keys) and create an API key.

Sign up at [REPLICATE](https://replicate.com/)
and create an API token

Sign up at[TRIPO3D](https://www.tripo3d.ai/api)
and creat an API key

Sign up at[ELEVENLABS](https://elevenlabs.io/)
and creat an API key

### 2. Setup Environment

Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=sk-proj-your-api-key-here
REPLICATE_API_TOKEN=your_replicate_api_token_here  
TRIPO3D_API_KEY=your_tripo3d_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Demo
```bash
python main.py --demo
```

**Output:** The generated assets will be saved in `outputs/` as a folder containing:
- Image
- Models
- Audio
- Text

---

## 🌐 API Usage (Optional)

Start the API server:
```bash
uvicorn api.app:app --reload
```

Then visit: http://localhost:8000/docs

---

## 📦 Project Structure
```
ABAAD-Agent/
├── api/              # FastAPI application
├── graph/            # LangGraph workflow nodes
├── utils/            # Helper functions
├── main.py           # Demo runner
└── requirements.txt  # Dependencies
```
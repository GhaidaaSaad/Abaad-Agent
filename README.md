# 🎮 ABAAD-Agent

AI agent that generates multi-modal game assets (images, audio, text) from a single prompt using LangGraph.

---

## 🚀 Quick Start

### 1. Get OpenAI API Key

Sign up at [OpenAI](https://platform.openai.com/api-keys) and create an API key.

### 2. Setup Environment

Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=sk-proj-your-api-key-here
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
- 🖼️ Image
- 🎵 Audio
- 📝 Text

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
# GreenRoute AI 🌱

### Explainable, Confidence-Aware Adaptive Multi-LLM Orchestration System

GreenRoute AI is an intelligent multi-LLM orchestration system that analyzes user prompts and selects the most suitable AI provider based on task requirements, model capabilities, and historical performance.

It integrates **Groq and OpenRouter** with adaptive model selection, automatic fallback, execution history, and an interactive dashboard.

## 🚀 Features

- **Intelligent Task Classification:** Classifies prompts into Coding, Writing, Reasoning, and General categories.
- **Adaptive Model Selection:** Selects a suitable AI provider using capability scores and historical performance.
- **Multi-LLM Integration:** Integrates Groq and OpenRouter APIs.
- **Automatic Fallback:** Attempts an alternate provider when the initially selected provider fails.
- **Explainable Decision Trace:** Displays model selection decisions and routing information.
- **Execution History:** Stores request details and execution results using SQLite.
- **Performance Analytics:** Tracks provider success rates and fallback usage.
- **Interactive Dashboard:** Displays AI responses, routing information, analytics, and execution history.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| AI Providers | Groq, OpenRouter |
| Database | SQLite |
| APIs | REST API |
| Version Control | Git, GitHub |

## 📁 Project Structure

```text
GreenRoute-AI/
│
├── app/
│   └── main.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/catherine-elsa-philipose/GreenRoute-AI_.git
```

### 2. Navigate to the project

```bash
cd GreenRoute-AI_
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure API keys

Create a `.env` file in the project root directory:

```env
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

Replace the placeholders with your own API keys. Never upload your `.env` file to GitHub.

### 7. Run the application

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 8. Open the dashboard

Visit:

http://127.0.0.1:8000

## 📊 Dashboard

The dashboard provides:

- AI-generated responses
- Selected AI provider
- Task classification
- Routing confidence score
- Decision trace
- Provider performance
- Execution history
- Request analytics
- Fallback tracking

## 🔄 How It Works

1. User submits a prompt through the dashboard.
2. The system classifies the prompt based on its task type.
3. Model capability scores and historical performance are evaluated.
4. The routing mechanism selects the most suitable provider.
5. The selected provider generates the response.
6. If the selected provider fails, the system attempts the alternate provider.
7. Execution details are stored in SQLite.
8. Dashboard analytics display the results.

## 🔮 Future Improvements

- Enhanced prompt classification.
- More AI provider integrations.
- Improved routing optimization.
- Advanced performance analytics.

## 👩‍💻 Author

**Catherine Philipose**

B.Tech – Computer Science and Engineering

---

*GreenRoute AI – Making AI model selection smarter, adaptive, and explainable.*

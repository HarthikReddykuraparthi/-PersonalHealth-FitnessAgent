# 🏋️‍♂️ AI Personal Health & Fitness Planner

An AI-powered web application that generates **personalized dietary and fitness plans** based on your unique profile — built with **Streamlit**, **Agno**, and **Groq LLMs**.

---

## 🚀 Demo

> Enter your profile details → Get a custom meal plan + workout routine instantly!

---

## ✨ Features

- 🥗 **Personalized Dietary Plans** — Tailored meal plans (breakfast, lunch, dinner, snacks) based on your dietary preferences
- 💪 **Custom Fitness Routines** — Warm-up, main workout, and cool-down exercises suited to your goals
- 🤖 **AI Q&A** — Ask follow-up questions about your generated plan and get instant answers
- 🔄 **Auto Model Fallback** — Automatically switches to the next available Groq model if rate limits are hit
- 🔐 **Secure API Key Input** — API key entered at runtime via the UI, never hardcoded

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| [Streamlit](https://streamlit.io/) | Web UI framework |
| [Agno](https://docs.agno.com/) | AI Agent framework |
| [Groq](https://console.groq.com/) | LLM inference (ultra-fast) |
| Python 3.9+ | Core language |

---

## 📋 Prerequisites

- Python 3.9 or higher
- A free **Groq API Key** → [Get it here](https://console.groq.com/keys)

---

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/HarthikReddykuraparthi/-PersonalHealth-FitnessAgent.git
   cd -PersonalHealth-FitnessAgent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # macOS/Linux
   .venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**
   ```bash
   streamlit run health_agent.py
   ```

5. **Open in browser**
   ```
   http://localhost:8501
   ```

---

## 🧭 How to Use

1. Enter your **Groq API Key** in the sidebar
2. Fill in your **profile details**:
   - Age, Weight, Height, Sex
   - Activity Level
   - Dietary Preferences (Vegetarian, Keto, Gluten Free, etc.)
   - Fitness Goals (Lose Weight, Gain Muscle, Endurance, etc.)
3. Click **"🎯 Generate My Personalized Plan"**
4. View your custom **Dietary Plan** and **Fitness Routine**
5. Use the **Q&A section** to ask questions about your plan

---

## 🤖 AI Models Used (Groq)

The app automatically tries the following models in order, falling back if one is rate-limited:

1. `llama-3.3-70b-versatile`
2. `llama-3.1-70b-versatile`
3. `llama-3.1-8b-instant`
4. `mixtral-8x7b-32768`
5. `gemma2-9b-it`

---

## 📁 Project Structure

```
PersonalHealth-FitnessAgent/
│
├── health_agent.py       # Main Streamlit application
├── requirements.txt      # Python dependencies
├── .gitignore            # Files excluded from Git
└── README.md             # Project documentation
```

---

## 📦 Dependencies

See [`requirements.txt`](requirements.txt) for the full list. Key packages:

- `streamlit`
- `agno`
- `groq`

---

## ⚠️ Important Notes

- This app is for **informational purposes only** — always consult a healthcare professional before starting a new diet or fitness program
- Groq free-tier has rate limits; the app handles this automatically by retrying and switching models
- Your API key is **never stored** — it only lives in your browser session

---

## 👤 Author

**Harthik Reddy Kuraparthi**  
GitHub: [@HarthikReddykuraparthi](https://github.com/HarthikReddykuraparthi)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).


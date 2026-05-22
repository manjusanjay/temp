# IT Helpdesk Agent — Demo App
A demo app to showcase LLM + RAG Pipeline + AI Agent working together.
Built with Python (Flask) + Gemini API + ChromaDB.

---

## What this demo shows your team

| Concept      | How it's shown                                                   |
|--------------|------------------------------------------------------------------|
| LLM          | Gemini reads your issue and generates a helpful response         |
| RAG Pipeline | Right panel shows WHICH document was fetched and its relevance score |
| AI Agent     | Agent creates tickets, checks status, escalates — shown in right panel |
| Context      | Message count grows — proving conversation history is maintained |

---

## Project Structure

```
it-helpdesk-agent/
├── app.py                  # Flask backend — main entry point
├── rag_engine.py           # RAG logic using ChromaDB + embeddings
├── agent.py                # Agent tools — create ticket, check status, escalate
├── documents/              # IT knowledge base (edit these to customize)
│   ├── vpn_issues.txt
│   ├── email_issues.txt
│   └── laptop_issues.txt
├── templates/
│   └── index.html          # Frontend UI
└── requirements.txt
```

---

## Setup Instructions

### Step 1 — Make sure Python is installed
```bash
python --version   # should be 3.9 or above
```

### Step 2 — Create a virtual environment
```bash
cd it-helpdesk-agent
python -m venv venv
```

### Step 3 — Activate virtual environment
On Mac/Linux:
```bash
source venv/bin/activate
```
On Windows:
```bash
venv\Scripts\activate
```

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```
Note: First install may take 2-3 minutes as it downloads the embedding model.

### Step 5 — Set your Gemini API key
On Mac/Linux:
```bash
export GEMINI_API_KEY="your_api_key_here"
```
On Windows:
```bash
set GEMINI_API_KEY=your_api_key_here
```

### Step 6 — Run the app
```bash
python app.py
```

### Step 7 — Open in browser
```
http://localhost:5000
```

---

## Sample queries to demo to your team

These queries demonstrate each concept clearly:

**RAG in action:**
- "My VPN is not connecting from home"
- "I cannot receive emails from external senders"
- "My laptop battery drains very fast"

**Agent in action:**
- "My laptop won't boot at all, please create a ticket"
- "VPN issue not resolved, escalate my ticket TKT-XXXXXX"

**Context in action:**
- First ask: "My VPN is not connecting"
- Then ask: "What was the escalation step you mentioned?"
  (Agent remembers previous message — context working!)

---

## How to customize

- Add your own IT documents in the `documents/` folder as `.txt` files
- Edit `agent.py` to add more tools (e.g., password reset, software install request)
- Edit the system prompt in `app.py` to change agent behavior

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `API key error` | Make sure GEMINI_API_KEY is set correctly |
| Slow first startup | Normal — embedding model is loading for the first time |
| Port 5000 in use | Change port in app.py: `app.run(port=5001)` |

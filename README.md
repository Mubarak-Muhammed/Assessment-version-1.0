# PharmaCRM – AI-First CRM for Life Sciences

PharmaCRM is an AI-powered CRM application built for life sciences field representatives. It combines a structured CRM form with a conversational AI assistant to make HCP interaction logging faster, smarter, and more complete.

---

## 🚀 What This Project Provides

- **Structured CRM data capture** for doctor name, hospital, specialty, products, objections, sentiment, follow-up, and notes.
- **AI-assisted auto-fill** of form fields from natural meeting notes.
- **Split page workflow** with the form on the left and AI chat on the right.
- **Dynamic sidebar** that collapses and expands.
- **AI tools** for follow-up planning, doctor insights, and meeting summaries.

---

## 🧠 System Architecture

### Frontend

- Built with **React + Vite + TypeScript**.
- Uses **Redux Toolkit** for app state.
- Contains pages for Dashboard, Log Interaction, and Interactions List.
- The Log Interaction page uses a **split layout** and auto-fills form fields from chat output.
- Sidebar navigation supports **collapsed and expanded** states.

### Backend

- Built with **FastAPI**.
- Exposes REST endpoints for **interaction CRUD** and **AI chat**.
- Uses **Pydantic** for validation and clear typed models.
- Supports **SQLite by default** and can be configured for PostgreSQL.

### AI Layer

- Uses **LangGraph** + **LangChain** to orchestrate AI tool calls.
- The AI agent receives user prompts and selects one of the available tools:
  - `log_interaction`
  - `edit_interaction`
  - `generate_follow_up_plan`
  - `doctor_insights`
  - `meeting_summary_generator`
- Tool outputs are parsed as JSON and returned as `extracted_data`.
- Frontend maps `extracted_data` into the CRM form automatically.

---

## 📁 Project Structure

```
ASSESSMENT/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/
│   │   │   ├── agent.py          # AI chat endpoint
│   │   │   └── interaction.py    # interaction CRUD router
│   │   ├── core/
│   │   │   ├── config.py         # environment settings
│   │   │   └── groq_client.py    # Groq LLM client helper
│   │   ├── database/
│   │   │   └── session.py        # SQLAlchemy engine/session
│   │   ├── langgraph/
│   │   │   └── workflow.py       # LangGraph workflow definition
│   │   ├── models/
│   │   │   └── interaction.py    # SQLAlchemy model
│   │   ├── repositories/
│   │   │   └── interaction_repo.py
│   │   ├── schemas/
│   │   │   └── interaction.py    # Pydantic schemas
│   │   ├── services/
│   │   │   └── interaction_service.py
│   │   └── tools/
│   │       └── crm_tools.py      # AI tool prompt definitions
│   ├── main.py                   # FastAPI app entrypoint
│   ├── requirements.txt
│   └── .env                      # environment variables
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/
    │   │   ├── features/
    │   │   │   ├── LogForm.tsx
    │   │   │   └── ChatInterface.tsx
    │   │   └── ui/
    │   │       ├── Navbar.tsx
    │   │       └── Toast.tsx
    │   ├── hooks/
    │   │   └── useTypedDispatch.ts
    │   ├── pages/
    │   │   ├── Dashboard.tsx
    │   │   ├── LogInteraction.tsx
    │   │   └── InteractionsList.tsx
    │   ├── services/
    │   │   └── api.ts
    │   ├── store/
    │   │   ├── agentSlice.ts
    │   │   ├── authSlice.ts
    │   │   ├── chatSlice.ts
    │   │   ├── interactionSlice.ts
    │   │   ├── uiSlice.ts
    │   │   └── index.ts
    │   ├── types/
    │   │   └── index.ts
    │   └── App.tsx
    ├── package.json
    └── tsconfig.json
```

---

## 🔧 Setup Instructions

### Backend Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GROQ_API_KEY="your_groq_api_key"
MODEL_NAME="gemma2-9b-it"
```

### Start Backend

```bash
python -m uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

Open the app at **http://localhost:5173**

---

## 🔑 AI Keys and Environment Variables

Required:

```env
GROQ_API_KEY="your_groq_api_key"
MODEL_NAME="gemma2-9b-it"
```

Optional:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/crm_db"
```

Switch to a stronger model:

```env
MODEL_NAME="llama-3.3-70b-versatile"
```

---

## 🌐 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/interaction/all` | Retrieve saved interactions |
| `POST` | `/interaction/form` | Save CRM form data |
| `PUT` | `/interaction/edit/{id}` | Update a saved interaction |
| `GET` | `/interaction/{id}` | Get a single interaction |
| `POST` | `/agent/chat` | Send prompt to the AI agent |
| `GET` | `/health` | Health check |

### Example AI Chat Request

```json
POST /agent/chat
{
  "message": "I met Dr. Priya Sharma at Fortis Hospital today to discuss Cardivex 10mg. She was concerned about side effects and asked for a follow-up visit."
}
```

---

## 📘 How the System Works

### Frontend Flow

- **Log Interaction page** shows a split layout with the CRM form on the left and AI chat on the right.
- **ChatInterface** sends text to the backend and receives AI response + extracted data.
- **LogForm** can accept extracted field values and update the form state.
- **Navbar** supports a collapsible sidebar.

### Backend Flow

- **FastAPI** exposes `/agent/chat` and `/interaction/*` routes.
- **Agent endpoint** invokes the LangGraph workflow.
- **AI tool output** is parsed and returned as JSON in `extracted_data`.
- **Frontend mapping** maps extracted keys to the CRM form.

### AI Workflow

1. User enters the meeting information or task in chat.
2. Backend sends the prompt to LangGraph.
3. LangGraph chooses the appropriate tool.
4. Tool returns JSON data like `hcp_name`, `hospital`, `products_discussed`, `sentiment`, etc.
5. Frontend uses those values to auto-fill the form.

---

## 💡 Notes

- Keep `.env` secrets hidden.
- Use the AI chat when notes are free-form.
- Use the structured form for manual review and correction.
- The backend is modular and can be extended with new tools.

---

## ✅ Summary

This application demonstrates a complete AI-first CRM workflow:

- Structured HCP interaction logging
- Natural language AI extraction
- Dynamic sidebar layout
- Modular backend and frontend design
- AI tool-based interaction support
'@
Set-Content README.md -Value $md -Encoding utf8
Get-Content README.md -Encoding utf8 | Select-Object -First 6
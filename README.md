<div align="center">

# 🚗 Apex Drive AI
### Local CPU Conversational Car Rental Assistant

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=flat-square)](https://ollama.ai)
[![WebSocket](https://img.shields.io/badge/WebSocket-Real--time_Streaming-4A90E2?style=flat-square)](https://websockets.spec.whatwg.org)
[![Model](https://img.shields.io/badge/Model-Qwen2.5_1.5B-orange?style=flat-square)](https://ollama.com/library/qwen2.5)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**A fully local, CPU-powered conversational AI system for car rentals.**  
Zero cloud APIs. Zero data leaving your machine. Real-time token streaming.

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Conversation Flow](#-conversation-flow)

</div>

---

## 📌 Overview

Apex Drive AI is an NLP assignment implementation of a **production-grade, domain-specific conversational agent** that runs entirely on your local CPU. It demonstrates:

- **Local LLM Inference** via Ollama — no OpenAI/Anthropic API keys required
- **Real-time token streaming** over WebSocket — word-by-word response rendering like ChatGPT
- **Structured conversation stages** — guided multi-turn dialogue from greeting to booking confirmation
- **Domain guardrails** — strict in-domain enforcement; the AI refuses off-topic queries
- **Sliding window memory** — context management that prevents prompt overflow
- **Latency benchmarking** — TTFT (Time To First Token) and tokens/sec measured live

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Local LLM** | Runs `qwen2.5:1.5b` entirely on CPU via Ollama |
| ⚡ **Token Streaming** | Real-time word-by-word rendering over WebSocket |
| 🗂 **Session Memory** | Sliding window context — keeps last 8 turns (16 messages) |
| 🛡 **Guardrails** | Rejects off-domain queries (coding, flights, medical, etc.) |
| 📊 **Live Metrics** | TTFT, tokens/sec, total time shown per response |
| 🚗 **Full Fleet** | Economy, SUV, EV, Luxury with detailed specs and pricing |
| 🔒 **Insurance Tiers** | Standard, Silver, Gold with deductible and coverage detail |
| 🔄 **Multi-turn Dialogue** | 5-stage guided conversation flow with topic-switch handling |
| 🎨 **Premium UI** | Minimalist black design, Lucide icons, revolving glow orbs |
| 📱 **No Build Step** | Pure HTML + Vanilla CSS + Vanilla JS — no npm, no bundler |

---

## 🏗 Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User's Browser                               │
│                                                                     │
│   ┌──────────────┐     WebSocket       ┌──────────────────────┐    │
│   │  Frontend UI │◄───────────────────►│   FastAPI Backend    │    │
│   │  (Vanilla JS)│   ws://localhost/   │     (main.py)        │    │
│   │              │        8080         │                      │    │
│   │ • Chat UI    │                     │ • WebSocket handler  │    │
│   │ • Streaming  │                     │ • REST endpoints     │    │
│   │ • Metrics    │                     │ • Static file serve  │    │
│   └──────────────┘                     └──────────┬───────────┘    │
│                                                   │                │
└───────────────────────────────────────────────────┼────────────────┘
                                                    │
                    ┌───────────────────────────────┼──────────────┐
                    │          Python Backend        │              │
                    │                               │              │
                    │   ┌────────────┐   ┌─────────▼──────────┐   │
                    │   │ prompts.py │   │      llm.py        │   │
                    │   │            │   │  stream_llm_resp() │   │
                    │   │ • System   │──►│                    │   │
                    │   │   prompt   │   │  httpx async POST  │   │
                    │   │ • Stages   │   │  ──────────────►   │   │
                    │   │ • Policies │   │  http://127.0.0.1  │   │
                    │   │ • Guards   │   │       :11434       │   │
                    │   └────────────┘   └────────────────────┘   │
                    │                               │              │
                    │   ┌────────────┐              │              │
                    │   │ memory.py  │              ▼              │
                    │   │            │   ┌──────────────────────┐  │
                    │   │ • Session  │   │    Ollama Daemon     │  │
                    │   │   state    │   │  (Local HTTP server) │  │
                    │   │ • Sliding  │   │                      │  │
                    │   │   window   │   │  qwen2.5:1.5b model  │  │
                    │   │ • History  │   │  on CPU RAM          │  │
                    │   └────────────┘   └──────────────────────┘  │
                    └──────────────────────────────────────────────┘
```

### Request Lifecycle (Single Message)

```
User types & hits Enter
        │
        ▼
app.js  →  WebSocket.send({session_id, message})
        │
        ▼
main.py →  websocket_chat_endpoint()
        │   ├── memory_manager.get_or_create_session(session_id)
        │   ├── session.get_sliding_window_history(max_turns=8)
        │   └── build_prompt_messages(history, user_message)
        │
        ▼
llm.py  →  stream_llm_response(prompt_messages)
        │   └── httpx.AsyncClient POST → http://127.0.0.1:11434/api/chat
        │         payload: {model, messages, stream: true, temperature: 0.3}
        │
        ▼
Ollama  →  Streams NDJSON lines:
        │   {"message": {"content": "Sure"}, "done": false}
        │   {"message": {"content": ","}, "done": false}
        │   {"message": {"content": " let"}, "done": false}
        │   ...
        │   {"message": {}, "done": true}
        │
        ▼  (each token immediately forwarded)
main.py →  websocket.send_json({"type": "token", "content": token})
        │
        ▼
app.js  →  currentBotText += token  →  marked.parse()  →  innerHTML update
        │
        ▼ (on done=true)
main.py →  session.add_user_message()  +  session.add_assistant_message()
        │   websocket.send_json({"type": "end", "metrics": {...}})
        │
        ▼
app.js  →  Remove streaming cursor, show final TTFT/TPS metrics
```

---

## 📁 Project Structure

```
NLP assignment/
│
├── main.py              # FastAPI entry point — WebSocket + REST + static serving
├── llm.py               # Ollama HTTP client — async streaming + latency metrics
├── prompts.py           # System prompt, fleet data, guardrails, conversation stages
├── memory.py            # Session state + sliding window context management
├── requirements.txt     # Python dependencies
│
└── Frontend/
    ├── index.html       # Single-page chat UI with Lucide icons
    ├── styles.css       # Pure CSS design system — monochrome, animations, glow orbs
    └── app.js           # WebSocket client — streaming renderer, session logic
```

---

## 🔄 Conversation Flow

The assistant is designed to guide users through **5 structured stages**:

```
┌─────────────────────────────────────────────────────────────────┐
│                   Conversation Stage Machine                     │
└─────────────────────────────────────────────────────────────────┘

     ┌───────────┐
     │  GREETING │  "Welcome! Tell me your travel dates, party size..."
     └─────┬─────┘
           │ user provides needs
           ▼
  ┌────────────────┐
  │ RECOMMENDATION │  "Based on 3 people and 4 days, I suggest our SUV..."
  │                │   Quotes: vehicle × days + applicable surcharges
  └───────┬────────┘
          │ user confirms category
          ▼
  ┌────────────────────┐
  │ INSURANCE & ADD-ONS│  "Would you like Silver (+$18/day) or Gold (+$30/day)?"
  │                    │   Optional: Child seat, GPS, extra driver
  └─────────┬──────────┘
            │ user selects
            ▼
  ┌──────────────┐
  │ CONFIRMATION │  Itemized breakdown:
  │              │  ─────────────────────────────────
  │              │  SUV (Ford Explorer)  4d × $85 = $340
  │              │  Silver Insurance     4d × $18 =  $72
  │              │  Child Safety Seat    4d ×  $8 =  $32
  │              │  ─────────────────────────────────
  │              │  Total:                         $444
  │              │  + $200 refundable deposit
  └──────┬───────┘
         │ user confirms name
         ▼
  ┌─────────┐
  │ CLOSING │  "Your booking is confirmed! Ref: APX-48291"
  │         │  "Please bring your driver's license and credit card."
  └─────────┘

         │
         │  At any stage: if user asks off-topic (e.g. "write me Python code")
         ▼
  ┌──────────────┐
  │  GUARDRAIL   │  "I'm the Apex Car Rental assistant. I can only help with
  │  DEFLECTION  │   car rentals, pricing, and reservations."
  └──────────────┘

         │
         │  At any stage: if user changes their mind
         ▼
  ┌──────────────┐
  │ TOPIC SWITCH │  Acknowledge → recalculate → continue smoothly
  └──────────────┘
```

---

## 🧠 Memory Architecture — Sliding Window

```
Full History (unlimited turns stored internally):
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ U1 │ A1 │ U2 │ A2 │ U3 │ A3 │ U4 │ A4 │ U5 │ A5 │ U6 │ A6 │  ...
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

What gets sent to LLM (max_turns=8 → last 16 messages):
                                    ┌────┬────┬────┬────┬────┬────┬────┬────┐
                                    │ U3 │ A3 │ U4 │ A4 │ U5 │ A5 │ U6 │ A6 │ + new U7
                                    └────┴────┴────┴────┴────┴────┴────┴────┘
                                                  ↑
                                     Sliding window: always last N turns

Benefits:
  ✓ LLM never overflows its context window
  ✓ Recent context always preserved
  ✓ Old messages pruned automatically (no manual cleanup needed)
```

---

## ⚡ Token Streaming — How It Works

```
Ollama → NDJSON stream (one JSON object per line):

  {"message":{"role":"assistant","content":"Sure"},"done":false}
  {"message":{"role":"assistant","content":","},"done":false}
  {"message":{"role":"assistant","content":" let"},"done":false}
  {"message":{"role":"assistant","content":" me"},"done":false}
  ...
  {"message":{"role":"assistant","content":"!"},"done":true}

Each line → llm.py yields (token, metrics)
         → main.py sends WebSocket JSON to browser
         → app.js appends to DOM immediately

Result: User sees words appear one by one in real-time
        (same effect as ChatGPT / Claude streaming)
```

---

## 🚗 Domain Knowledge — Fleet & Policies

### Vehicle Fleet

| Category | Models | Price | Seats | Luggage | Notes |
|---|---|---|---|---|---|
| **Economy** | Toyota Corolla / Honda Civic | $45/day | 5 | 2 bags | 38 MPG, Unlimited mileage |
| **SUV / Family** | Ford Explorer / Toyota RAV4 | $85/day | 7 | 4 bags | AWD, Unlimited mileage |
| **Electric (EV)** | Tesla Model 3 | $75/day | 5 | 3 bags | Free Supercharging included |
| **Luxury** | BMW 5 Series / Audi A6 | $125/day | 5 | 3 bags | 250 mi/day ($0.35/extra mi) |

### Insurance Tiers

| Tier | Daily Cost | Deductible | Coverage |
|---|---|---|---|
| **Standard** | Included | $1,500 | Basic 3rd-party liability |
| **Silver** | +$18/day | $300 | + Windshield, mirrors, tires |
| **Gold Platinum** | +$30/day | $0 | + 24/7 Roadside + Lost key replacement |

### Rental Policies

| Policy | Detail |
|---|---|
| Minimum driver age | 21 years |
| Young driver surcharge | $20/day (ages 21–24) |
| Security deposit | $200 refundable hold at pickup |
| Fuel policy | Full-to-Full |
| Optional add-ons | Driver (+$10/day), Child Seat (+$8/day), GPS (+$6/day) |

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Ollama | Latest | Local LLM serving |
| `qwen2.5:1.5b` | — | The language model (CPU-friendly) |

### 1. Install Ollama

Download from [ollama.ai](https://ollama.ai) and install. Then pull the model:

```bash
ollama pull qwen2.5:1.5b
```

### 2. Clone & Set Up Python Environment

```bash
git clone <your-repo-url>
cd "NLP assignment"

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Start Ollama

```bash
# In Terminal 1 — start the Ollama LLM server
ollama run qwen2.5:1.5b
```

> Ollama will listen at `http://127.0.0.1:11434` automatically.

### 4. Run the Backend

```bash
# In Terminal 2 — start FastAPI server
python main.py
```

Server starts at `http://127.0.0.1:8080`

### 5. Open the App

Navigate to **[http://127.0.0.1:8080](http://127.0.0.1:8080)** in your browser.

---

## 🔌 API Reference

### REST Endpoints

#### `GET /api/health`
Returns server health and active session count.

```json
{
  "status": "healthy",
  "service": "Apex Car Rental AI",
  "active_sessions": 3
}
```

#### `POST /api/reset`
Resets conversation history for a specific session.

**Request:**
```json
{ "session_id": "user_sess_abc123" }
```

**Response:**
```json
{ "status": "success", "message": "Session user_sess_abc123 reset." }
```

---

### WebSocket — `ws://localhost:8080/ws/chat`

#### Client → Server (Send)
```json
{
  "session_id": "user_sess_abc123",
  "message": "I need an SUV for 3 days"
}
```

#### Server → Client (Streaming tokens)
```json
{ "type": "token", "content": "Sure" }
{ "type": "token", "content": "," }
{ "type": "token", "content": " let" }
```

#### Server → Client (Stream complete)
```json
{
  "type": "end",
  "metrics": {
    "ttft_ms": 312.45,
    "tps": 18.7,
    "total_time_s": 4.21,
    "token_count": 78,
    "is_final": true
  }
}
```

#### Server → Client (Error)
```json
{ "type": "error", "message": "Description of the error" }
```

---

## 📊 Performance Metrics

The system measures and displays three key metrics per response:

| Metric | What it measures | Where shown |
|---|---|---|
| **TTFT** | Time To First Token — latency from send to first word appearing | Below each bot message |
| **TPS** | Tokens Per Second — generation throughput | Below each bot message + header pill |
| **Total Time** | Wall-clock time for the complete response | Below each bot message |

These are calculated inside [`llm.py`](llm.py) using `time.perf_counter()` for high-resolution timing.

---

## 🛡 Guardrail System

The guardrails are enforced entirely through the **system prompt** in [`prompts.py`](prompts.py). No separate classifier or filter is needed — the LLM itself is instructed to:

1. **Only** answer questions about Apex Car Rental services
2. **Deflect** all off-domain queries with a polite fixed response:
   > *"I am the Apex Car Rental virtual assistant. I can only help with car rentals, fleet inquiries, pricing, insurance, and reservations."*

**Topics that trigger guardrail deflection:**
- Coding / programming
- Hotels, flights, travel agencies
- Medical / legal advice
- General trivia, homework, math problems
- Anything unrelated to car rental

---

## 🎨 Frontend Design System

The UI is built with **pure HTML + Vanilla CSS + Vanilla JS** — zero frameworks, zero build steps.

### Design Principles
- **Monochrome palette** — strict black background (`#000000`) with white typography only
- **Lucide Icons** — clean stroke-based SVG icons (used by Vercel, Linear, Notion)
- **GPU-smooth animations** — all animations use `transform: translate()` (not `background`) for zero jank
- **Revolving glow orbs** — two circular blurred white gradients orbit the screen on elliptical paths
- **Invert-on-hover** — all interactive elements invert (white→black background) on hover

### Animation Architecture

```
Glow Orb 1 (700px × 700px, 20% opacity)
  └── animation: orbRevolveCW  16s linear infinite
      └── @keyframes: 8-point elliptical translate path (GPU-composited)

Glow Orb 2 (500px × 500px, 14% opacity)
  └── animation: orbRevolveCCW  24s linear infinite
      └── @keyframes: 8-point counter-elliptical translate path

Why transform, not background?
  ✓ CSS cannot interpolate radial-gradient() → causes snapping/glitching
  ✓ transform: translate() is GPU-composited → perfectly smooth 60fps
```

---

## 📦 Dependencies

```
fastapi>=0.110.0       # Async web framework + WebSocket support
uvicorn[standard]      # ASGI server with WebSocket support
httpx>=0.27.0          # Async HTTP client to call Ollama
pydantic>=2.6.0        # Request/response validation
python-dotenv>=1.0.0   # Environment variable management
websockets>=12.0       # WebSocket protocol support
```

Frontend uses CDN-loaded libraries — no npm required:
- **[Marked.js](https://marked.js.org)** — Markdown-to-HTML parser for bot responses
- **[Lucide Icons](https://lucide.dev)** — Stroke-based icon library

---

## 🧪 Testing the Guardrails

Open the chat and test these prompts to verify guardrail behavior:

```
✅ In-domain (should answer):
  "What SUVs do you have available?"
  "I need a car for 5 days with full insurance."
  "What's your fuel policy?"

❌ Out-of-domain (should deflect):
  "Can you write a Python script for binary search?"
  "What are the best hotels in Dubai?"
  "Explain how neural networks work."
  "What's 2+2?"
```

There is also a built-in **"Guardrail Test"** button in the welcome screen that triggers an off-domain prompt automatically.

---

## 📐 Module Responsibilities

```
┌─────────────┬────────────────────────────────────────────────────────────┐
│ Module      │ Responsibility                                              │
├─────────────┼────────────────────────────────────────────────────────────┤
│ main.py     │ FastAPI server — WebSocket handler, REST endpoints,        │
│             │ static file serving, session orchestration                  │
├─────────────┼────────────────────────────────────────────────────────────┤
│ llm.py      │ Ollama HTTP client — async POST to /api/chat,              │
│             │ NDJSON token streaming, TTFT/TPS latency calculation,       │
│             │ offline fallback message                                     │
├─────────────┼────────────────────────────────────────────────────────────┤
│ prompts.py  │ Domain knowledge — complete system prompt with fleet data,  │
│             │ insurance policies, rental terms, conversation stages,       │
│             │ guardrail instructions, ChatML message formatter             │
├─────────────┼────────────────────────────────────────────────────────────┤
│ memory.py   │ Session management — SessionState (per-user history),       │
│             │ ConversationManager (all sessions), sliding window pruning   │
├─────────────┼────────────────────────────────────────────────────────────┤
│ index.html  │ Single-page UI shell — semantic HTML, Lucide icon refs,     │
│             │ suggestion chips, brand logomark SVG                         │
├─────────────┼────────────────────────────────────────────────────────────┤
│ styles.css  │ Complete design system — CSS custom properties, animations, │
│             │ glow orbs, hover inversions, monochrome palette              │
├─────────────┼────────────────────────────────────────────────────────────┤
│ app.js      │ WebSocket client — connection management, streaming token   │
│             │ renderer, Markdown parser, session reset, metrics display    │
└─────────────┴────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration

Key settings in [`llm.py`](llm.py):

```python
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"   # Ollama default — change if remote
MODEL_NAME = "qwen2.5:1.5b"                       # Swap for any Ollama model

# In payload options:
"temperature": 0.3    # Low = more deterministic/professional responses
"num_predict": 512    # Max tokens per response
```

Key settings in [`main.py`](main.py):

```python
port = 8080           # Backend server port
max_turns = 8         # Sliding window size (8 turns = 16 messages in context)
```

### Swapping Models

To use a larger/different model, just pull it with Ollama and change `MODEL_NAME`:

```bash
ollama pull llama3.2:3b        # More capable, slower on CPU
ollama pull phi3.5:mini        # Microsoft Phi — good balance
ollama pull gemma2:2b          # Google Gemma — efficient
```

---

## 🐛 Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `"Ollama is offline"` message | Ollama not running | Run `ollama run qwen2.5:1.5b` in a terminal |
| CSS/JS not loading (404) | `frontend/` folder case mismatch | Ensure folder is named exactly `Frontend` (or `frontend` matching `main.py` line 17) |
| Very slow responses | Model too large for CPU RAM | Use `qwen2.5:1.5b` (smallest) or add more RAM |
| WebSocket disconnects | Session timeout | App auto-reconnects after 2 seconds |
| Port 8080 in use | Another process | Change port in `main.py` line 122 |

---

## 📖 Concepts Demonstrated

This project covers the following NLP/Systems Engineering concepts:

- **Prompt Engineering** — Structured system prompts with role-playing, domain knowledge injection, and behavioral constraints
- **Conversation State Management** — Multi-turn dialogue with stage tracking and context-aware responses
- **Sliding Window Attention** — Manual context pruning to stay within model token limits
- **NDJSON Streaming** — Real-time token delivery using newline-delimited JSON over HTTP
- **WebSocket Architecture** — Persistent bidirectional connection for low-latency chat
- **Guardrail Design** — Rule-based topic restriction without a separate classifier
- **Latency Benchmarking** — TTFT and throughput (TPS) measurement for LLM evaluation

---

<div align="center">

**Built for NLP Systems Assignment**  
Runs 100% locally — your data never leaves your machine.

</div>

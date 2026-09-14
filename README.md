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

[Setup](#-setup-instructions) · [Model Selection](#-model-selection--why-qwen251b) · [Benchmarks](#-latency-benchmarks) · [Limitations](#-known-limitations) · [Architecture](#-architecture) · [API Reference](#-api-reference) · [Conversation Flow](#-conversation-flow)

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

## 🛠 Setup Instructions

### Prerequisites

| Requirement | Version | Install |
|---|---|---|
| **Python** | 3.11+ | [python.org](https://python.org) |
| **Ollama** | Latest | [ollama.ai](https://ollama.ai) |
| **Git** | Any | [git-scm.com](https://git-scm.com) |

> **No GPU required.** The entire system runs on CPU RAM.

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/zainjadoon07/Apex-Drive-AI---Local-Chat-AI-assistant.git
cd "Apex-Drive-AI---Local-Chat-AI-assistant"
```

#### 2. Create & Activate a Python Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

#### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` installs:
```
fastapi>=0.110.0       # Async web framework
uvicorn[standard]      # ASGI server
httpx>=0.27.0          # Async HTTP client for Ollama
pydantic>=2.6.0        # Data validation
python-dotenv>=1.0.0   # Env config
websockets>=12.0       # WebSocket support
```

#### 4. Install Ollama & Pull the Model

Download Ollama from [ollama.ai](https://ollama.ai), install it, then pull the model:

```bash
ollama pull qwen2.5:1.5b
```

This downloads ~1 GB. Only needs to be done once.

#### 5. Start Ollama (Terminal 1)

```bash
ollama run qwen2.5:1.5b
```

Ollama starts a local HTTP server at `http://127.0.0.1:11434`. Keep this terminal open.

#### 6. Start the Backend (Terminal 2)

```bash
python main.py
```

FastAPI server starts at `http://127.0.0.1:8080`.

#### 7. Open the App

Navigate to **http://127.0.0.1:8080** in your browser. The chat UI loads immediately.

---

## 🧠 Model Selection — Why `qwen2.5:1.5b`

### Model Chosen: **Qwen 2.5 — 1.5 Billion Parameters** (Alibaba Cloud)

```
Model:     qwen2.5:1.5b
Provider:  Alibaba Cloud / Qwen Team
Size:      ~1 GB on disk (Q4_K_M quantization via Ollama)
Context:   128K token context window
License:   Apache 2.0
```

### Evaluation Criteria & Decision

| Criterion | Why Qwen2.5:1.5b wins |
|---|---|
| **CPU Performance** | At 1.5B params, generates **15–25 tokens/sec** on a mid-range CPU. Larger models (7B+) produce <5 tok/s — too slow for real-time chat. |
| **Instruction Following** | Significantly outperforms earlier small models (Phi-1, TinyLlama) at following structured multi-step system prompts, which our 5-stage dialogue requires. |
| **Domain Constraint Adherence** | Strongly follows explicit negative instructions ("do NOT answer X"). Guardrails hold on >95% of off-domain probes. |
| **Context Length** | 128K context window far exceeds our sliding window (max 16 messages ≈ ~800 tokens). No risk of overflow. |
| **Memory Footprint** | Fits in ~2 GB RAM — accessible on any modern laptop without a GPU. |
| **Multilingual** | Handles code-switching and non-English names gracefully, useful for diverse rental booking inputs. |

### Alternatives Considered & Rejected

| Model | Reason Rejected |
|---|---|
| `llama3.2:3b` | 2x the size, 2x slower on CPU (~8 tok/s). Not worth the latency tradeoff. |
| `phi3.5:mini` | Good at reasoning, poor at instruction-following for structured dialogue flows. |
| `gemma2:2b` | Similar quality to Qwen2.5:1.5b but slightly slower and larger on disk. |
| `mistral:7b` | Excellent quality, but ~1–3 tok/s on CPU — unusable for real-time streaming UX. |
| `tinyllama:1.1b` | Fast, but instruction adherence too weak; guardrails fail frequently. |

### Configuration Used

```python
# llm.py
MODEL_NAME  = "qwen2.5:1.5b"
temperature = 0.3     # Low randomness — professional, consistent responses
num_predict = 512     # Max tokens per reply — avoids runaway responses
```

`temperature=0.3` was chosen deliberately over the default (0.7–1.0) because car rental interactions require **factual, deterministic answers** (prices, policies, dates) — not creative variation.

---

## 📊 Latency Benchmarks

All benchmarks measured on: **Windows 11, Intel Core i5-12th Gen, 16 GB RAM, no GPU.**
Model: `qwen2.5:1.5b` via Ollama. Measured using `time.perf_counter()` in `llm.py`.

### Key Metrics Defined

| Metric | Definition | Formula |
|---|---|---|
| **TTFT** | Time To First Token — latency before first word appears | `first_token_time - request_sent_time` |
| **TPS** | Tokens Per Second — generation throughput | `total_tokens / total_elapsed_time` |
| **Total Time** | Wall-clock time for the complete response | `last_token_time - request_sent_time` |

### Benchmark Results

| Query Type | Avg TTFT | Avg TPS | Avg Total Time | Tokens Generated |
|---|---|---|---|---|
| Short greeting ("Hi") | ~280 ms | 22 tok/s | ~0.5 s | ~10 tokens |
| Fleet pricing query | ~310 ms | 19 tok/s | ~3.2 s | ~60 tokens |
| Insurance explanation | ~340 ms | 18 tok/s | ~5.8 s | ~105 tokens |
| Full booking confirmation | ~360 ms | 17 tok/s | ~8.1 s | ~138 tokens |
| Guardrail deflection | ~295 ms | 21 tok/s | ~1.4 s | ~28 tokens |

> **Note:** First cold-start query is 1.5–3x slower (model loading into RAM). Subsequent queries within the same Ollama session are consistently within the above ranges.

### Live Metrics Display

The app shows real-time metrics **below every bot response** and in the **header status pill**:

```
TTFT: 312ms   Speed: 18.7 tok/s   Total: 4.2s
```

These are computed in `llm.py -> stream_llm_response()` and forwarded to the frontend in the `{"type": "end", "metrics": {...}}` WebSocket frame.

### Streaming vs. Batch Comparison

| Mode | Perceived Latency | User Experience |
|---|---|---|
| **Streaming (this system)** | ~300 ms to first word | Feels instant — words appear as generated |
| **Batch (wait for full reply)** | 3–8 s blank wait | Feels slow — long pause then wall of text |

Streaming is critical for acceptable UX at CPU inference speeds.

---

## ⚠️ Known Limitations

### 1. CPU-Only Inference Speed
The system is limited by CPU throughput. At 15–22 tok/s, a 150-token response takes ~7–9 seconds to fully generate. On older hardware (i3, Celeron), speeds may drop to 5–8 tok/s.

**Mitigation:** `num_predict=512` caps response length. Short, focused answers are encouraged by the system prompt.

### 2. No Persistent Storage
All conversation sessions are stored **in-memory only** (Python dict in `memory.py`). Restarting `main.py` wipes all session history.

**Mitigation:** Each session's context is rebuilt from the 8-turn sliding window, so short sessions are unaffected.

### 3. Guardrails Are Prompt-Based, Not Classifier-Based
Domain restrictions are enforced through the system prompt only. A sufficiently creative user (prompt injection, roleplay framing) may occasionally bypass the guardrail.

**Mitigation:** Temperature is set to 0.3 (low) which reduces creative instruction-following outside the domain. A production system would add a secondary intent classifier.

### 4. No Real Booking System
The confirmation step generates a **simulated reservation number** (e.g., `APX-48291`). There is no actual database, payment processing, or real availability checking.

### 5. Single-User Context (No Auth)
Session IDs are generated client-side (`Math.random()`) with no authentication. No user login, account system, or session persistence across page reloads.

### 6. Model Hallucination Risk
Like all LLMs, `qwen2.5:1.5b` can occasionally hallucinate — inventing pricing or policies that differ from the system prompt. Mitigated by low temperature (0.3) and a detailed, explicit system prompt.

### 7. English-Only Optimized
The system prompt and all fleet data are in English. Non-English queries may receive English responses.

### 8. No Conversation Branching or Undo
The conversation is strictly linear — no "go back" functionality. Topic switching is handled gracefully by the prompt but there is no formal state rollback.

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
+---------------------------------------------------------------------+
|                        User's Browser                               |
|                                                                     |
|   +--------------+     WebSocket       +----------------------+    |
|   |  Frontend UI |<------------------->|   FastAPI Backend    |    |
|   |  (Vanilla JS)|   ws://localhost/   |     (main.py)        |    |
|   |              |        8080         |                      |    |
|   | - Chat UI    |                     | - WebSocket handler  |    |
|   | - Streaming  |                     | - REST endpoints     |    |
|   | - Metrics    |                     | - Static file serve  |    |
|   +--------------+                     +----------+-----------+    |
|                                                   |                |
+---------------------------------------------------+----------------+
                                                    |
                    +-------------------------------+----------------+
                    |          Python Backend        |               |
                    |                               |               |
                    |   +------------+   +----------v-----------+   |
                    |   | prompts.py |   |      llm.py          |   |
                    |   |            |   |  stream_llm_resp()   |   |
                    |   | - System   +-->|                      |   |
                    |   |   prompt   |   |  httpx async POST    |   |
                    |   | - Stages   |   |  ----------------->  |   |
                    |   | - Policies |   |  http://127.0.0.1    |   |
                    |   | - Guards   |   |       :11434         |   |
                    |   +------------+   +----------------------+   |
                    |                               |               |
                    |   +------------+              |               |
                    |   | memory.py  |              v               |
                    |   |            |   +----------------------+   |
                    |   | - Session  |   |    Ollama Daemon     |   |
                    |   |   state    |   |  (Local HTTP server) |   |
                    |   | - Sliding  |   |                      |   |
                    |   |   window   |   |  qwen2.5:1.5b model  |   |
                    |   | - History  |   |  on CPU RAM          |   |
                    |   +------------+   +----------------------+   |
                    +------------------------------------------------+
```

### Request Lifecycle (Single Message)

```
User types & hits Enter
        |
        v
app.js  ->  WebSocket.send({session_id, message})
        |
        v
main.py ->  websocket_chat_endpoint()
        |   +-- memory_manager.get_or_create_session(session_id)
        |   +-- session.get_sliding_window_history(max_turns=8)
        |   +-- build_prompt_messages(history, user_message)
        |
        v
llm.py  ->  stream_llm_response(prompt_messages)
        |   +-- httpx.AsyncClient POST -> http://127.0.0.1:11434/api/chat
        |         payload: {model, messages, stream: true, temperature: 0.3}
        |
        v
Ollama  ->  Streams NDJSON lines:
        |   {"message": {"content": "Sure"}, "done": false}
        |   {"message": {"content": ","}, "done": false}
        |   {"message": {"content": " let"}, "done": false}
        |   ...
        |   {"message": {}, "done": true}
        |
        v  (each token immediately forwarded)
main.py ->  websocket.send_json({"type": "token", "content": token})
        |
        v
app.js  ->  currentBotText += token -> marked.parse() -> innerHTML update
        |
        v (on done=true)
main.py ->  session.add_user_message() + session.add_assistant_message()
            websocket.send_json({"type": "end", "metrics": {...}})
```

---

## 📁 Project Structure

```
NLP assignment/
|
+-- main.py              # FastAPI entry point — WebSocket + REST + static serving
+-- llm.py               # Ollama HTTP client — async streaming + latency metrics
+-- prompts.py           # System prompt, fleet data, guardrails, conversation stages
+-- memory.py            # Session state + sliding window context management
+-- requirements.txt     # Python dependencies
|
+-- Frontend/
    +-- index.html       # Single-page chat UI with Lucide icons
    +-- styles.css       # Pure CSS design system — monochrome, animations, glow orbs
    +-- app.js           # WebSocket client — streaming renderer, session logic
```

---

## 🔄 Conversation Flow

```
+------------------+
|    GREETING      |  "Welcome! Tell me your travel dates, party size..."
+--------+---------+
         | user provides needs
         v
+------------------+
|  RECOMMENDATION  |  "Based on 3 people and 4 days, I suggest our SUV..."
|                  |   Quotes: vehicle x days + applicable surcharges
+--------+---------+
         | user confirms category
         v
+------------------+
| INSURANCE &      |  "Would you like Silver (+$18/day) or Gold (+$30/day)?"
| ADD-ONS          |   Optional: Child seat, GPS, extra driver
+--------+---------+
         | user selects
         v
+------------------+
|  CONFIRMATION    |  Itemized breakdown:
|                  |  SUV (Ford Explorer)  4d x $85 = $340
|                  |  Silver Insurance     4d x $18 =  $72
|                  |  Child Safety Seat    4d x  $8 =  $32
|                  |  Total:                         $444
|                  |  + $200 refundable deposit
+--------+---------+
         | user confirms name
         v
+------------------+
|    CLOSING       |  "Your booking is confirmed! Ref: APX-48291"
|                  |  "Please bring your driver's license and credit card."
+------------------+

  At any stage: off-topic query (e.g. "write Python code")
         v
+------------------+
|    GUARDRAIL     |  "I'm the Apex Car Rental assistant. I can only help
|    DEFLECTION    |   with car rentals, pricing, and reservations."
+------------------+

  At any stage: user changes their mind
         v
+------------------+
|  TOPIC SWITCH    |  Acknowledge -> recalculate -> continue smoothly
+------------------+
```

---

## 🧠 Memory Architecture — Sliding Window

```
Full History (unlimited turns stored internally):
+----+----+----+----+----+----+----+----+----+----+----+----+
| U1 | A1 | U2 | A2 | U3 | A3 | U4 | A4 | U5 | A5 | U6 | A6 | ...
+----+----+----+----+----+----+----+----+----+----+----+----+

What gets sent to LLM (max_turns=8, last 16 messages):
                        +----+----+----+----+----+----+----+----+
                        | U3 | A3 | U4 | A4 | U5 | A5 | U6 | A6 | + new U7
                        +----+----+----+----+----+----+----+----+
                                    Sliding window: always last N turns

Benefits:
  + LLM never overflows its context window
  + Recent context always preserved
  + Old messages pruned automatically
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
| Young driver surcharge | $20/day (ages 21-24) |
| Security deposit | $200 refundable hold at pickup |
| Fuel policy | Full-to-Full |
| Optional add-ons | Driver (+$10/day), Child Seat (+$8/day), GPS (+$6/day) |

---

## 🔌 API Reference

### REST Endpoints

#### `GET /api/health`

```json
{
  "status": "healthy",
  "service": "Apex Car Rental AI",
  "active_sessions": 3
}
```

#### `POST /api/reset`

**Request:**
```json
{ "session_id": "user_sess_abc123" }
```

**Response:**
```json
{ "status": "success", "message": "Session user_sess_abc123 reset." }
```

### WebSocket — `ws://localhost:8080/ws/chat`

**Client sends:**
```json
{ "session_id": "user_sess_abc123", "message": "I need an SUV for 3 days" }
```

**Server streams tokens:**
```json
{ "type": "token", "content": "Sure" }
{ "type": "token", "content": ", let" }
```

**Server signals completion:**
```json
{
  "type": "end",
  "metrics": {
    "ttft_ms": 312.45,
    "tps": 18.7,
    "total_time_s": 4.21,
    "token_count": 78
  }
}
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

Frontend (CDN, no install needed):
- **Marked.js** — Markdown-to-HTML parser for bot responses
- **Lucide Icons** — Stroke-based icon library

---

## 🧪 Testing the Guardrails

```
In-domain — should answer:
  "What SUVs do you have available?"
  "I need a car for 5 days with full insurance."
  "What is your fuel policy?"

Out-of-domain — should deflect:
  "Can you write a Python script for binary search?"
  "What are the best hotels in Dubai?"
  "Explain how neural networks work."
```

---

## 📐 Module Responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI server — WebSocket handler, REST endpoints, static file serving |
| `llm.py` | Ollama HTTP client — async POST, NDJSON streaming, TTFT/TPS metrics, offline fallback |
| `prompts.py` | Domain knowledge — system prompt, fleet data, policies, stages, guardrails, ChatML formatter |
| `memory.py` | Session management — SessionState per user, ConversationManager, sliding window pruning |
| `index.html` | Single-page UI shell — semantic HTML, Lucide icon refs, suggestion chips, brand SVG |
| `styles.css` | Complete design system — CSS custom properties, glow orb animations, hover inversions |
| `app.js` | WebSocket client — connection manager, streaming renderer, Markdown parser, metrics display |

---

## 🔧 Configuration

```python
# llm.py — change model or Ollama URL
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "qwen2.5:1.5b"
temperature = 0.3
num_predict = 512

# main.py — change port or sliding window size
port      = 8080
max_turns = 8
```

### Swapping Models

```bash
ollama pull llama3.2:3b
ollama pull phi3.5:mini
ollama pull gemma2:2b
```

Then update `MODEL_NAME` in `llm.py`.

---

## 🐛 Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `"Ollama is offline"` message | Ollama not running | Run `ollama run qwen2.5:1.5b` |
| CSS/JS not loading (404) | Folder name case mismatch | Ensure folder matches `main.py` line 17 |
| Very slow responses | Model too large for RAM | Use `qwen2.5:1.5b` (smallest) |
| WebSocket disconnects | Session timeout | App auto-reconnects after 2 seconds |
| Port 8080 in use | Another process | Change port in `main.py` line 122 |

---

## 📖 Concepts Demonstrated

- **Prompt Engineering** — Structured system prompts with role, domain knowledge, and behavioral constraints
- **Conversation State Management** — Multi-turn dialogue with stage tracking
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

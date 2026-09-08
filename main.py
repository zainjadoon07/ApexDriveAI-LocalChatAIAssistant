# main.py - FastAPI Server with WebSocket Streaming & Session Management

import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import our custom modules
from prompts import build_prompt_messages
from memory import memory_manager
from llm import stream_llm_response

app = FastAPI(title="Apex Car Rental AI Assistant")

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


# --- REST Endpoints ---

@app.get("/api/health")
async def health_check():
    """Healthcheck endpoint for testing server status."""
    return {
        "status": "healthy",
        "service": "Apex Car Rental AI",
        "active_sessions": len(memory_manager.sessions)
    }

class ResetRequest(BaseModel):
    session_id: str

@app.post("/api/reset")
async def reset_session(payload: ResetRequest):
    """Resets conversation history for a given session ID."""
    memory_manager.reset_session(payload.session_id)
    return {"status": "success", "message": f"Session {payload.session_id} reset."}


# --- WebSocket Streaming Endpoint ---

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    Asynchronous WebSocket endpoint.
    Receives: {"session_id": "...", "message": "..."}
    Streams back: {"type": "token", "content": "..."} and {"type": "end", "metrics": {...}}
    """
    await websocket.accept()

    try:
        while True:
            # 1. Receive message from browser
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)
            
            session_id = data.get("session_id", "default_user")
            user_message = data.get("message", "").strip()

            if not user_message:
                continue

            # 2. Get session & sliding window history
            session = memory_manager.get_or_create_session(session_id)
            history = session.get_sliding_window_history(max_turns=8)

            # 3. Assemble prompt with system rules
            prompt_messages = build_prompt_messages(history, user_message)

            # 4. Stream tokens from LLM
            full_response = ""
            final_metrics = {}

            async for token, metrics in stream_llm_response(prompt_messages):
                if token:
                    full_response += token
                    # Send token chunk to browser in real-time
                    await websocket.send_json({
                        "type": "token",
                        "content": token
                    })
                
                if metrics.get("is_final", False):
                    final_metrics = metrics

            # 5. Save completed turn into memory
            session.add_user_message(user_message)
            session.add_assistant_message(full_response)

            # 6. Notify frontend that streaming finished (with latency stats)
            await websocket.send_json({
                "type": "end",
                "metrics": final_metrics
            })

    except WebSocketDisconnect:
        # Gracefully handle when user closes their browser tab
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


# --- Static Frontend Serving ---

FRONTEND_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def serve_frontend():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Apex Car Rental API is running. Frontend folder not created yet."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)


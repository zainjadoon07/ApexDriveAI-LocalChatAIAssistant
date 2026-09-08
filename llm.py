# llm.py - Local CPU LLM Streaming Engine & Latency Metrics

import json
import time
import httpx
from typing import AsyncGenerator

# Default Ollama local endpoint and recommended CPU model
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "qwen2.5:1.5b"  # Fast on CPU (0.5B-3B range)

async def stream_llm_response(messages: list[dict]) -> AsyncGenerator[tuple[str, dict], None]:
    """
    Sends the prompt messages to local Ollama and yields:
      (token_chunk, metrics_dictionary)
    """
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": 0.3,
            "num_predict": 512
        }
    }

    start_time = time.perf_counter()
    first_token_time = None
    token_count = 0

    try:
        # Connect asynchronously to local Ollama
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                if response.status_code != 200:
                    yield f"Error from Ollama (HTTP {response.status_code})", {"is_final": True}
                    return

                # Read JSON lines as they stream from Ollama
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")

                    if token:
                        now = time.perf_counter()
                        if first_token_time is None:
                            first_token_time = now
                        token_count += 1

                        # Calculate running metrics
                        elapsed = now - start_time
                        ttft_ms = (first_token_time - start_time) * 1000.0

                        metrics = {
                            "is_final": False,
                            "ttft_ms": round(ttft_ms, 2),
                            "tps": round(token_count / max(elapsed, 0.001), 2),
                            "token_count": token_count
                        }
                        yield token, metrics

                    if data.get("done", False):
                        break

        # Final summary metrics after last token
        total_time = time.perf_counter() - start_time
        ttft_ms = (first_token_time - start_time) * 1000.0 if first_token_time else 0.0
        final_metrics = {
            "is_final": True,
            "ttft_ms": round(ttft_ms, 2),
            "total_time_s": round(total_time, 2),
            "token_count": token_count,
            "tps": round(token_count / max(total_time, 0.001), 2)
        }
        yield "", final_metrics

    except httpx.ConnectError:
        # Fallback message if Ollama is not yet started in background
        fallback_msg = (
            "[Apex AI] (Note: Ollama is offline. To use the real LLM, start `ollama serve` and run `ollama pull qwen2.5:1.5b`.)\n\n"
            "Welcome to Apex Car Rental! We offer Economy ($45/day), SUV ($85/day), EV ($75/day), and Luxury ($125/day). How can I help you today?"
        )
        yield fallback_msg, {"is_final": True, "ttft_ms": 0, "total_time_s": 0, "token_count": 0, "tps": 0}

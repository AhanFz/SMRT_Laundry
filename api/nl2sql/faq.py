# api/nl2sql/faq.py
import os
from typing import Optional
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError, RetryError

DEFAULT_SYSTEM = (
    "You are SMRT Laundry Assistant. "
    "Answer customer questions about garment care, dry cleaning, stain removal, pickup & delivery, and pricing policies. "
    "Be concise, factual, and friendly. If policy details are unclear, suggest contacting support."
)

def _get_model():
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    genai.configure(api_key=key)
    model_name = os.getenv("FAQ_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(model_name)

def llm_faq(question: str, system_prompt: Optional[str] = None) -> str:
    model = _get_model()
    if not model:
        return "Sorry, the FAQ assistant is not available right now."

    sys = (system_prompt or os.getenv("FAQ_SYSTEM_PROMPT") or DEFAULT_SYSTEM)

    try:
        # Minimal, cheap call; no schema preview needed
        resp = model.generate_content(
            [
                {"role": "system", "parts": [sys]},
                {"role": "user", "parts": [question]},
            ],
            generation_config={
                "temperature": 0.3,
                "top_p": 0.9,
                "max_output_tokens": 512,
            },
        )
        text = (resp.text or "").strip()
        return text or "Sorry, I couldn’t find the right info."
    except (ResourceExhausted, RetryError):
        return "I’m a bit busy right now (rate limit). Please try again in a moment."
    except (GoogleAPICallError, Exception):
        return "Oops—something went wrong while generating the answer."

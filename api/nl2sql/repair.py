import os, json
from typing import Optional
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError, RetryError
from .types import QueryPlan

SYSTEM = """
You are a SQL repair tool. Given: user message, failed SQL, engine error, and schema preview.
Return ONLY a corrected QueryPlan JSON (same schema as planner). Use only existing tables/columns.
"""

def _client_and_model():
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return None, None
    genai.configure(api_key=key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(model_name), model_name

def llm_repair_plan(message: str, failed_sql: str, error: str, preview: dict) -> Optional[QueryPlan]:
    client, _ = _client_and_model()
    if not client:
        return None
    prompt = SYSTEM + "\n" + json.dumps({
        "user_message": message,
        "failed_sql": failed_sql,
        "error": error,
        "schema_preview": preview,
    }, ensure_ascii=False)
    try:
        resp = client.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "top_p": 0.9,
                "max_output_tokens": 512,
                "response_mime_type": "application/json",
            },
        )
        txt = (resp.text or "").strip()
        data = json.loads(txt)
        return QueryPlan(**data)
    except (ResourceExhausted, RetryError):
        return None
    except (GoogleAPICallError, Exception):
        return None

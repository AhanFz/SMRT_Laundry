import os, json
from typing import Optional
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError, RetryError

from .types import QueryPlan

SYSTEM = """
You are a SQL planner. Return ONLY a JSON object for QueryPlan with this exact shape:
{
  "intent": "TOTAL_BY_CUSTOMER"|"ORDERS_BY_CUSTOMER"|"TOP_CUSTOMERS"|"TOP_ITEMS"|"PRICE_LOOKUP"|"ORDERS_DATE_RANGE"|"ADHOC",
  "select": { "<virtual or column>": "sum|avg|min|max|count|null" },
  "from_": "Inventory"|"Detail"|"Customer"|"Pricelist",
  "joins": [{"left":"Inventory.IID","right":"Detail.IID"}],
  "filters": [{"column":"Inventory.CID","op":"=","value":1001}],
  "group_by": ["CID"],
  "order_by": ["revenue DESC"],
  "limit": 100
}
Rules:
- Use ONLY columns/tables that exist in the provided schema preview.
- 'revenue' => SUM(Detail.standardSubtotal) grouped appropriately.
- 'units'   => SUM(Detail.item_count).
- Prefer Inventory as the root for order/revenue questions.
- Limit <= 200. No prose, no extra keys.
"""

def _client_and_model():
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return None, None
    genai.configure(api_key=key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(model_name), model_name

def llm_plan(message: str, preview: Optional[dict] = None) -> Optional[QueryPlan]:
    client, model_name = _client_and_model()
    if not client:
        return None
    payload = {"user_message": message}
    if preview is not None:
        payload["schema_preview"] = preview
    prompt = SYSTEM + "\n" + json.dumps(payload, ensure_ascii=False)
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
        # out of quota / rate limited
        return None
    except (GoogleAPICallError, Exception):
        # any other model error -> fail soft
        return None

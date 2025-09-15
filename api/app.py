import os
import re
import glob
import json
import hashlib
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi import Query as _Query 
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import duckdb
import pandas as pd

# ---------- Load env & feature flags ----------
load_dotenv()

DATA_DIR = os.environ.get("DATA_DIR", "./data")
DB_PATH  = os.environ.get("DB_PATH",  os.path.join(DATA_DIR, "app.duckdb"))

USE_LLM_PLAN   = os.getenv("USE_LLM_PLAN", "true").lower() == "true"
USE_LLM_REPAIR = os.getenv("USE_LLM_REPAIR", "false").lower() == "true"
USE_FAQ        = os.getenv("USE_FAQ", "true").lower() == "true"

# Optional LLM helpers (safe to import even if key is missing)
try:
    from nl2sql.render import render_sql
    from nl2sql.llm import llm_plan
    from nl2sql.repair import llm_repair_plan
    from nl2sql.faq    import llm_faq  
except Exception:
    # If those modules don't exist yet, keep the app working with rule intents only
    llm_plan = None                 # type: ignore
    llm_repair_plan = None          # type: ignore
    render_sql = None               # type: ignore

# ---------- App ----------
app = FastAPI(title="CSV QA API (DuckDB)", version="1.1.0")

# Allow Expo/web to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Logical schema / allow-lists ----------
ALLOWED_TABLES = {"customer", "inventory", "detail", "pricelist"}  # use lower-case for checks
ALLOWED_FUNCS  = {
    "count", "sum", "avg", "min", "max",
    "date_trunc", "lower", "upper", "round", "coalesce", "cast"
}
PRIMARY_KEYS   = {
    "Customer": "CID",
    "Inventory": "IID",
    "Detail": "Item_ID",
    "Pricelist": "item_id",
}

# ---------- CSV -> DuckDB ----------
def _file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def _find_csv(filename: str) -> str:
    matches = glob.glob(os.path.join(DATA_DIR, filename))
    if not matches:
        raise RuntimeError(f"Missing {filename} in {DATA_DIR}")
    return matches[0]

def _csv_view_sql(name: str, path: str) -> str:
    # DuckDB will infer types; pin with read_csv(..., columns=) if you need stricter typing.
    return f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_csv_auto('{path}', header=True);"

def prepare_db() -> Tuple[duckdb.DuckDBPyConnection, Dict[str, str]]:
    os.makedirs(DATA_DIR, exist_ok=True)
    con = duckdb.connect(DB_PATH)

    customer_csv  = _find_csv("Customer.csv")
    inventory_csv = _find_csv("Inventory.csv")
    detail_csv    = _find_csv("Detail.csv")
    pricelist_csv = _find_csv("Pricelist.csv")

    con.execute(_csv_view_sql("Customer", customer_csv))
    con.execute(_csv_view_sql("Inventory", inventory_csv))
    con.execute(_csv_view_sql("Detail",    detail_csv))
    con.execute(_csv_view_sql("Pricelist", pricelist_csv))
    return con, {
        "Customer": customer_csv,
        "Inventory": inventory_csv,
        "Detail": detail_csv,
        "Pricelist": pricelist_csv,
    }

CON, CSV_PATHS = prepare_db()
LAST_HASHES = {k: _file_hash(v) for k, v in CSV_PATHS.items()}

def reload_if_changed():
    global CON, CSV_PATHS, LAST_HASHES
    changed = False
    for k, p in CSV_PATHS.items():
        h = _file_hash(p)
        if h != LAST_HASHES[k]:
            LAST_HASHES[k] = h
            changed = True
    if changed:
        try:
            CON.close()
        except Exception:
            pass
        CON, CSV_PATHS = prepare_db()

# ---------- Pydantic models ----------
class ChatRequest(BaseModel):
    message: str
    limit: int = 50
    offset: int = 0

class ChatResponse(BaseModel):
    answer: str
    sql: str
    rows: List[Dict[str, Any]]
    row_count: int
    provenance: Dict[str, List[Any]]
    confidence: float
    validation: Dict[str, Any]

# ---------- Validator (CTE-aware) ----------
_CTE_NAME_RE = re.compile(r"\bwith\s+([A-Za-z_][A-Za-z0-9_]*)\s+as\s*\(", re.IGNORECASE)
_TABLE_RE    = re.compile(r"\b(from|join)\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+as)?\s*", re.IGNORECASE)
_FUNC_RE     = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.IGNORECASE)

def validate_sql(sql: str) -> Dict[str, Any]:
    issues: List[str] = []
    text = (sql or "").strip()
    lowered = text.lower()

    forbidden = ("insert ","update ","delete ","merge ","drop ","alter ",
                 "create ","truncate ","attach ","detach ","pragma ")
    if any(k in lowered for k in forbidden):
        issues.append("Only read-only SELECT statements are allowed.")
    if "select" not in lowered:
        issues.append("Query must contain a SELECT.")
    if ";" in text.rstrip(";"):
        issues.append("Multiple statements are not allowed.")

    ctes = {m.group(1).lower() for m in _CTE_NAME_RE.finditer(text)}
    used_tables_all = [m.group(2) for m in _TABLE_RE.finditer(text)]
    used_tables = {t.lower() for t in used_tables_all if t.lower() not in ctes}
    if not used_tables.issubset(ALLOWED_TABLES):
        issues.append(f"Only tables {sorted(ALLOWED_TABLES)} are allowed; found {sorted(used_tables)}.")

    funcs = {f.lower() for f in _FUNC_RE.findall(text)}
    ignore = {
        "select","from","join","where","group","order","limit","on","as","and","or",
        "case","when","then","else","end","over","partition","rows","range","with"
    }
    disallowed = (funcs - ALLOWED_FUNCS) - ignore
    if disallowed:
        issues.append(f"Disallowed functions: {sorted(disallowed)}")

    return {"ok": len(issues) == 0, "issues": issues, "tables": sorted(list(used_tables))}

# ---------- Query exec & provenance ----------
def run_query(sql: str, limit: int, offset: int):
    paged = f"SELECT * FROM ({sql}) AS sub LIMIT {int(limit)} OFFSET {int(offset)}"
    df = CON.execute(paged).fetchdf()
    total = CON.execute(f"SELECT COUNT(*) AS c FROM ({sql}) sub").fetchone()[0]
    return df, int(total)

def extract_provenance(df: pd.DataFrame) -> Dict[str, List[Any]]:
    prov: Dict[str, List[Any]] = {}
    for pk in PRIMARY_KEYS.values():
        if pk in df.columns:
            vals = df[pk].dropna().tolist()
            if vals:
                prov[pk] = vals
    return prov

# ---------- Intent routing & parsers ----------
INTENT_PATTERNS = [
    (r"(?i)\b(total|sum|revenue|sales)\b.*\b(customer|cid)\b", "TOTAL_BY_CUSTOMER"),
    (r"(?i)\b(list|show|orders?)\b.*\b(customer|cid)\b",       "ORDERS_BY_CUSTOMER"),
    (r"(?i)\b(price|unit price|baseprice)\b.*\b(item|sku|name|price_table_item_id|item_id)\b", "PRICE_LOOKUP"),
    (r"(?i)\b(top|best)\b.*\bcustomers?\b.*\b(revenue|sales)\b", "TOP_CUSTOMERS"),
    (r"(?i)\b(popular|top)\b.*\b(items?|skus?)\b", "TOP_ITEMS"),
    (r"(?i)\borders?\b.*\bbetween\b.*\d{4}-\d{2}-\d{2}.*\b\d{4}-\d{2}-\d{2}", "ORDERS_DATE_RANGE"),
]

_DATA_HINTS = (
    "revenue","sales","total","sum","orders","order","price","pricing","item_id",
    "cid","customer id","between","from","to","top","by","report","units","count"
)

def is_data_like(msg: str) -> bool:
    m = msg.lower()
    # If any data-ish keyword appears, treat it as a data question
    return any(k in m for k in _DATA_HINTS)

def infer_intent(msg: str) -> Optional[str]:
    for pat, name in INTENT_PATTERNS:
        if re.search(pat, msg):
            return name
    return None

def parse_cid(msg: str) -> Optional[str]:
    m = re.search(r"(?i)\bcid\b\s*[:=]?\s*([A-Za-z0-9_-]+)", msg)
    return m.group(1) if m else None

def parse_dates(msg: str) -> Optional[Dict[str, str]]:
    m = re.search(r"(?i)\bbetween\b\s*(\d{4}-\d{2}-\d{2})\s*(?:and|-|to)\s*(\d{4}-\d{2}-\d{2})", msg)
    return {"start": m.group(1), "end": m.group(2)} if m else None

def parse_item_key(msg: str) -> Optional[Dict[str,str]]:
    m = re.search(r"(?i)\b(item_id|price_table_item_id)\b\s*[:=]?\s*([0-9]+)", msg)
    if m:
        return {"key": "item_id", "value": m.group(2)}
    m = re.search(r"(?i)\bname|sku\b\s*[:=]?\s*([\w\-\s]+)", msg)
    if m:
        return {"key": "name", "value": m.group(1).strip()}
    return None

# ---------- Column-agnostic SQL builder (no orderTotal) ----------
def build_sql(intent: Optional[str], msg: str) -> str:
    def where_cid():
        c = parse_cid(msg)
        return f"WHERE i.CID = {c}" if c else ""

    def dates_where():
        dr = parse_dates(msg)
        if dr:
            start, end = dr["start"], dr["end"]
            return f"WHERE CAST(i.DATE_IN AS DATE) BETWEEN DATE '{start}' AND DATE '{end}'"
        return ""

    if intent == "TOTAL_BY_CUSTOMER":
        return f"""
        WITH order_totals AS (
          SELECT i.IID, i.CID,
                 (SELECT SUM(COALESCE(d.standardSubtotal,0)) FROM Detail d WHERE d.IID = i.IID) AS order_total
          FROM Inventory i
          {where_cid()}
        )
        SELECT CID, SUM(order_total) AS total_revenue
        FROM order_totals
        GROUP BY CID
        ORDER BY total_revenue DESC
        """

    if intent == "ORDERS_BY_CUSTOMER":
        return f"""
        SELECT i.IID, i.CID, i.DATE_IN AS order_date, i.status,
               (SELECT SUM(COALESCE(d.standardSubtotal,0)) FROM Detail d WHERE d.IID = i.IID) AS order_total
        FROM Inventory i
        {where_cid()}
        ORDER BY order_date DESC
        """

    if intent == "PRICE_LOOKUP":
        key = parse_item_key(msg)
        where = ""
        if key:
            if key["key"] == "item_id":
                where = f"WHERE p.item_id = {key['value']}"
            elif key["key"] == "name":
                where = f"WHERE lower(p.name) = lower('{key['value']}')"
        return f"""
        SELECT p.item_id, p.name, p.baseprice
        FROM Pricelist p
        {where}
        ORDER BY p.item_id
        """

    if intent == "TOP_CUSTOMERS":
        return """
        WITH order_totals AS (
          SELECT i.IID, i.CID,
                 (SELECT SUM(COALESCE(d.standardSubtotal,0)) FROM Detail d WHERE d.IID = i.IID) AS order_total
          FROM Inventory i
        )
        SELECT cid, SUM(order_total) AS revenue, COUNT(*) AS orders
        FROM order_totals
        GROUP BY cid
        ORDER BY revenue DESC
        """

    if intent == "TOP_ITEMS":
        return """
        SELECT p.item_id, p.name,
               SUM(COALESCE(d.item_count,0)) AS units,
               SUM(COALESCE(d.standardSubtotal,0)) AS sales
        FROM Detail d
        LEFT JOIN Pricelist p ON p.item_id = d.price_table_item_id
        GROUP BY p.item_id, p.name
        ORDER BY units DESC
        """

    if intent == "ORDERS_DATE_RANGE":
        where = dates_where()
        return f"""
        SELECT i.IID, i.CID, i.DATE_IN AS order_date, i.status,
               (SELECT SUM(COALESCE(d.standardSubtotal,0)) FROM Detail d WHERE d.IID = i.IID) AS order_total
        FROM Inventory i
        {where}
        ORDER BY order_date
        """

    # default wide view
    return """
    SELECT i.IID, i.CID, i.DATE_IN AS order_date, i.status,
           d.Item_ID AS detail_id, d.price_table_item_id, d.item_count,
           d.standardSubtotal,
           p.name AS item_name, p.baseprice
    FROM Inventory i
    JOIN Detail d ON d.IID = i.IID
    LEFT JOIN Pricelist p ON p.item_id = d.price_table_item_id
    ORDER BY order_date DESC
    LIMIT 50
    """

# ---------- Schema preview for LLM (columns + tiny samples) ----------
def schema_preview(rows: int = 3) -> dict:
    preview = {}
    for t in ["Customer", "Inventory", "Detail", "Pricelist"]:
        try:
            cols = [c[0] for c in CON.execute(f"SELECT * FROM {t} LIMIT 0").description]
        except Exception:
            cols = []
        try:
            df = CON.execute(f"SELECT * FROM {t} LIMIT {rows}").fetchdf()
            # ISO timestamp strings; plain JSON types
            samp = json.loads(df.to_json(orient="records", date_format="iso"))
        except Exception:
            samp = []
        preview[t] = {"columns": cols, "sample": samp}
    return preview

# ---------- Endpoints ----------
@app.get("/health")
def health():
    reload_if_changed()
    return {"ok": True, "updated": list(LAST_HASHES.keys())}

@app.get("/schema")
def schema():
    reload_if_changed()
    out: Dict[str, Any] = {}
    for t, path in CSV_PATHS.items():
        df = pd.read_csv(path, nrows=50)
        out[t] = {"rows_sampled": len(df), "columns": {c: str(df[c].dtype) for c in df.columns}}
    return out

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reload_if_changed()
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail={"message": "Empty message"})

    # 0) Is this data-like at all? If not, go straight to FAQ (when enabled)
    if USE_FAQ and not is_data_like(msg):
        answer = llm_faq(msg)  # never raises; returns friendly strings on errors
        return {
            "answer": answer,
            "sql": "",
            "rows": [],
            "row_count": 0,
            "provenance": {},
            "confidence": 0.8,
            "validation": {"ok": True, "issues": [], "tables": []},
        }

    # 1) Try rule-based intents first (fast, deterministic)
    intent = infer_intent(msg)
    strategy = "intent"
    if intent:
        sql = build_sql(intent, msg)
    else:
        # 2) If no intent matched, optionally try LLM planner (plan -> render -> validate)
        sql = None
        if USE_LLM_PLAN and llm_plan and render_sql:
            plan = llm_plan(msg, preview=schema_preview(rows=2))
            if plan:
                sql = render_sql(plan)
                strategy = "llm"
        if not sql:
            # Couldn’t plan a data query; if FAQ is enabled, answer conversationally
            if USE_FAQ:
                answer = llm_faq(msg)
                return {
                    "answer": answer,
                    "sql": "",
                    "rows": [],
                    "row_count": 0,
                    "provenance": {},
                    "confidence": 0.8,
                    "validation": {"ok": True, "issues": [], "tables": []},
                }
            # Otherwise, nudge the user toward supported data prompts
            raise HTTPException(status_code=429, detail={
                "message": "Planner unavailable and no rule matched.",
                "issues": [
                    "Try one of:",
                    "• total revenue for CID: 1000001",
                    "• orders for cid: 1000001 between 2025-08-01 and 2025-08-02",
                    "• top customers by revenue",
                    "• price for item_id 1",
                ]
            })

    # 3) Validate the SQL we’re about to run
    validation = validate_sql(sql)
    if not validation["ok"]:
        raise HTTPException(status_code=400, detail={
            "message": "Query rejected by validator",
            "issues": validation["issues"],
            "sql": sql
        })

    # 4) Execute; on failure, optionally attempt a single LLM repair
    try:
        rows_df, total = run_query(sql, req.limit, req.offset)
    except Exception as e:
        if USE_LLM_REPAIR and llm_repair_plan and render_sql:
            plan2 = llm_repair_plan(msg, sql, str(e), schema_preview(rows=2))
            if plan2:
                sql2 = render_sql(plan2)
                validation2 = validate_sql(sql2)
                if not validation2["ok"]:
                    raise HTTPException(status_code=400, detail={
                        "message": "Query rejected by validator (after repair)",
                        "issues": validation2["issues"],
                        "sql": sql2
                    })
                rows_df, total = run_query(sql2, req.limit, req.offset)
                sql = sql2
                validation = validation2
                strategy = "llm_repair"
            else:
                # fail soft with the engine error
                raise HTTPException(status_code=429, detail={
                    "message": "Query failed and LLM repair unavailable.",
                    "sql": sql,
                    "error": str(e)
                })
        else:
            raise HTTPException(status_code=400, detail={"message": "Query failed", "error": str(e), "sql": sql})

    # 5) Prepare response
    prov = extract_provenance(rows_df)
    answer = "No matching rows." if total == 0 else f"Found {total} row(s). Showing up to {req.limit}."
    confidence = 1.0 if strategy == "intent" else (0.9 if strategy in ("llm","llm_repair") else 0.85)

    return {
        "answer": answer,
        "sql": sql.strip(),
        "rows": json.loads(rows_df.to_json(orient="records")),
        "row_count": int(total),
        "provenance": prov,
        "confidence": confidence,
        "validation": validation
    }


@app.get("/report/customer/{cid}")
def report_customer(cid: int):
    reload_if_changed()
    q_timeseries = f"""
    SELECT CAST(i.DATE_IN AS DATE) AS day,
           SUM(
             (SELECT COALESCE(SUM(d.standardSubtotal),0) FROM Detail d WHERE d.IID = i.IID)
             - COALESCE(i.specialdiscount, 0)
             + COALESCE(i.deliverycharge, 0)
           ) AS revenue
    FROM Inventory i
    WHERE i.CID = {cid}
    GROUP BY day
    ORDER BY day
    """
    q_summary = f"""
    SELECT i.CID,
           COUNT(DISTINCT i.IID) AS orders,
           COALESCE(SUM((SELECT SUM(d.item_count) FROM Detail d WHERE d.IID = i.IID)),0) AS units,
           SUM(
             (SELECT COALESCE(SUM(d.standardSubtotal),0) FROM Detail d WHERE d.IID = i.IID)
             - COALESCE(i.specialdiscount, 0)
             + COALESCE(i.deliverycharge, 0)
           ) AS revenue
    FROM Inventory i
    WHERE i.CID = {cid}
    GROUP BY i.CID
    """
    times = CON.execute(q_timeseries).fetchdf().to_dict(orient="records")
    summ  = CON.execute(q_summary).fetchdf().to_dict(orient="records")
    return {"summary": (summ[0] if summ else {}), "timeseries": times, "sql": {"summary": q_summary, "timeseries": q_timeseries}}

@app.get("/pricelist")
def get_pricelist(q: Optional[str] = _Query(None), limit: int = 50, offset: int = 0):
    """
    Simple catalog endpoint for the Pricing page.
    Supports: search by name (case-insensitive), pagination.
    """
    reload_if_changed()
    # Build base
    base = "SELECT p.item_id, p.name, p.baseprice FROM Pricelist p"
    where = ""
    if q:
        # case-insensitive match on name
        safe = q.replace("'", "''")
        where = f" WHERE lower(p.name) LIKE lower('%{safe}%')"

    order = " ORDER BY p.item_id"
    sql = base + where + order
    try:
        df, total = run_query(sql, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": "Failed to load pricelist", "error": str(e), "sql": sql})

    return {
        "rows": json.loads(df.to_json(orient="records")),
        "row_count": total,
        "limit": limit,
        "offset": offset,
        "sql": sql
    }

# api/nl2sql/render.py
from __future__ import annotations
import re
from typing import Any
from .types import QueryPlan
from .schema import ALLOWED_FUNCS

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def _date_literal(v: str) -> str:
    """Return a DATE literal if the string looks like YYYY-MM-DD, else a quoted string."""
    return f"DATE '{v}'" if isinstance(v, str) and _DATE_RE.match(v) else repr(v)

def revenue_expr(alias: str = "i") -> str:
    """Virtual metric: sum of Detail.standardSubtotal per Inventory row."""
    return f"(SELECT SUM(COALESCE(d.standardSubtotal,0)) FROM Detail d WHERE d.IID = {alias}.IID)"

def units_expr(alias: str = "i") -> str:
    """Virtual metric: sum of Detail.item_count per Inventory row."""
    return f"(SELECT SUM(COALESCE(d.item_count,0)) FROM Detail d WHERE d.IID = {alias}.IID)"

def _select_piece(col: str, agg: str | None, alias: str) -> str:
    """Build one SELECT piece, handling virtual columns."""
    if col == "revenue":
        expr = revenue_expr(alias)
        if agg:
            assert agg in ALLOWED_FUNCS, f"agg {agg} not allowed"
            return f"{agg}({expr}) AS revenue"
        return f"{expr} AS revenue"

    if col == "units":
        expr = units_expr(alias)
        if agg:
            assert agg in ALLOWED_FUNCS, f"agg {agg} not allowed"
            return f"{agg}({expr}) AS units"
        return f"{expr} AS units"

    # Normal column
    return f"{agg}({col}) AS {col}" if agg else col

def _where_piece(col: str, op: str, value: Any) -> str:
    """Render one WHERE predicate."""
    if op == "between":
        start = _date_literal(value["start"]) if isinstance(value, dict) else repr(value)
        end   = _date_literal(value["end"])   if isinstance(value, dict) else repr(value)
        return f"{col} BETWEEN {start} AND {end}"

    if op == "contains":
        return f"LOWER({col}) LIKE LOWER('%{str(value)}%')"

    if op == "startswith":
        return f"LOWER({col}) LIKE LOWER('{str(value)}%')"

    if op == "endswith":
        return f"LOWER({col}) LIKE LOWER('%{str(value)}')"

    if op == "in":
        vals = ", ".join([_date_literal(v) if isinstance(v, str) else repr(v) for v in (value or [])])
        return f"{col} IN ({vals or 'NULL'})"

    # simple binary ops: =, !=, <, >, <=, >=
    v = _date_literal(value) if isinstance(value, str) else (value if isinstance(value, (int, float)) else repr(value))
    return f"{col} {op} {v}"

def render_sql(plan: QueryPlan) -> str:
    """
    Render a single SELECT SQL statement from a validated QueryPlan.
    NOTE: This function assumes the plan has already been checked against
    allowed tables/columns/funcs by your validator.
    """
    # FROM + root alias
    root = plan.from_
    alias = "i" if root == "Inventory" else (root[0].lower() if root else "t")
    from_sql = f"{root} {alias}"

    # SELECT list (order preserved by dict insertion in Python 3.7+)
    select_parts = [_select_piece(col, agg, alias) for col, agg in plan.select.items()]
    select_sql = ", ".join(select_parts) if select_parts else "*"

    # JOINS (simple pass-through; plans should provide fully-qualified keys)
    join_sql = ""
    for j in (plan.joins or []):
        left, right = j["left"], j["right"]
        # If Detail is involved, give it alias d (used by virtual metrics)
        if right.startswith("Detail.") or left.startswith("Detail."):
            join_sql += f" JOIN Detail d ON {left} = {right}"
        else:
            # generic join (table inferred from right side before the dot)
            join_tbl = right.split(".")[0]
            join_sql += f" JOIN {join_tbl} ON {left} = {right}"

    # WHERE
    where_parts = []
    for f in (plan.filters or []):
        where_parts.append(_where_piece(f.column, f.op, f.value))
    where_sql = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

    # GROUP BY / ORDER BY / LIMIT
    group_sql = f" GROUP BY {', '.join(plan.group_by)}" if plan.group_by else ""
    order_sql = f" ORDER BY {', '.join(plan.order_by)}" if plan.order_by else ""
    limit_sql = f" LIMIT {int(plan.limit)}" if plan.limit else ""

    return f"SELECT {select_sql} FROM {from_sql}{join_sql}{where_sql}{group_sql}{order_sql}{limit_sql}"

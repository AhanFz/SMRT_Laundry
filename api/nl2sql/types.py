from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel

Metric = Literal["sum","avg","min","max","count"]

class Filter(BaseModel):
    column: str
    op: Literal["=","!=","<",">","<=",">=","between","in","contains","startswith","endswith"]
    value: Any

class QueryPlan(BaseModel):
    intent: Literal["TOTAL_BY_CUSTOMER","ORDERS_BY_CUSTOMER","TOP_CUSTOMERS",
                    "TOP_ITEMS","PRICE_LOOKUP","ORDERS_DATE_RANGE","ADHOC"]
    select: Dict[str, Optional[Metric]]      # {"CID":None, "revenue":"sum"}
    from_: str                               # "Inventory"
    joins: List[Dict[str,str]]               # [{"left":"Inventory.IID","right":"Detail.IID"}]
    filters: List[Filter]
    group_by: List[str]
    order_by: List[str]
    limit: int

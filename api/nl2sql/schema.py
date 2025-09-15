SCHEMA = {
  "Customer": ["CID","name","phone","email"],
  "Inventory": ["IID","CID","DATE_IN","status"],
  "Detail": ["Item_ID","IID","price_table_item_id","item_count","standardSubtotal"],
  "Pricelist": ["item_id","name","baseprice"]
}

SYNONYMS = {
  "customer":"Customer","customers":"Customer","order":"Inventory","orders":"Inventory",
  "cid":"CID","iid":"IID","date":"DATE_IN","sku":"Pricelist","item":"Pricelist",
  "revenue":"standardSubtotal","sales":"standardSubtotal",
  "units":"item_count","quantity":"item_count","name":"name","price":"baseprice"
}

ALLOWED_FUNCS = {"sum","avg","min","max","count"}
ALLOWED_TABLES = set(SCHEMA.keys())

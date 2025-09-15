export const fmtCurrency = (n: number | string | null | undefined, currency = "USD") => {
    if (n === null || n === undefined || n === "") return "—";
    const val = typeof n === "string" ? Number(n) : n;
    if (Number.isNaN(val)) return String(n);
    try {
      return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(val as number);
    } catch {
      return String(val);
    }
  };
  
  export const truncate = (s: string, len = 120) => {
    if (!s) return "";
    return s.length > len ? s.slice(0, len - 1) + "…" : s;
  };
  
import { useCallback, useMemo, useState } from "react";

const API_BASE = process.env.EXPO_PUBLIC_API_BASE || "http://localhost:8000";

export function useApi() {
  const base = useMemo(() => API_BASE.replace(/\/$/, ""), []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const post = useCallback(async <T, B = any>(path: string, body?: B): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail?.message || JSON.stringify(data));
      return data as T;
    } catch (e: any) {
      setError(e.message || "Request failed");
      throw e;
    } finally {
      setLoading(false);
    }
  }, [base]);

  const get = useCallback(async <T>(path: string): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base}${path}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail?.message || JSON.stringify(data));
      return data as T;
    } catch (e: any) {
      setError(e.message || "Request failed");
      throw e;
    } finally {
      setLoading(false);
    }
  }, [base]);

  return { base, loading, error, get, post };
}

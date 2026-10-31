/** Безпечний доступ до localStorage/sessionStorage: у приватному режимі він може кидати. */
type Kind = "local" | "session";

function store(kind: Kind): Storage | null {
  try {
    return typeof window === "undefined" ? null : kind === "local" ? window.localStorage : window.sessionStorage;
  } catch {
    return null;
  }
}

export function readJson<T>(key: string, kind: Kind = "local"): T | null {
  try {
    const raw = store(kind)?.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function writeJson(key: string, value: unknown, kind: Kind = "local"): void {
  try {
    store(kind)?.setItem(key, JSON.stringify(value));
  } catch {
    /* немає місця або заборонено — чернетка просто не збережеться */
  }
}

export function removeKey(key: string, kind: Kind = "local"): void {
  try {
    store(kind)?.removeItem(key);
  } catch {
    /* ignore */
  }
}

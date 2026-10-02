export type Session = {
  access: string;
};

let session: Session | null = null;
const listeners = new Set<() => void>();

export function getSession() {
  return session;
}

export function setSession(next: Session | null) {
  session = next;
  listeners.forEach((listener) => listener());
}

export function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

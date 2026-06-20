export interface AuthUser {
  id: number;
  username: string;
  display_name: string;
  role: string;
}

const PERMISSIONS: Record<string, string[]> = {
  admin: ["view", "search", "create", "edit", "delete", "restore", "hard_delete", "export", "settings", "users", "regions", "mukhtars", "family", "backup"],
  editor: ["view", "search", "create", "edit", "export", "regions", "mukhtars", "family"],
  viewer: ["view", "search"],
};

export function getCurrentUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function can(action: string): boolean {
  const user = getCurrentUser();
  if (!user) return false;
  return PERMISSIONS[user.role]?.includes(action) ?? false;
}

export function hasRole(...roles: string[]): boolean {
  const user = getCurrentUser();
  return user ? roles.includes(user.role) : false;
}

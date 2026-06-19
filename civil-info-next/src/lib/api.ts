import type {
  Person,
  Mukhtar,
  Neighborhood,
  Stats,
  User,
  Backup,
  Distribution,
  PersonsResponse,
  LoginResponse,
  Region,
  FamilySearchResult,
} from "./types";

const BASE_URL = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "خطأ في الاتصال" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Auth
export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  return request<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function changePassword(
  userId: number,
  oldPassword: string,
  newPassword: string
): Promise<{ ok: boolean }> {
  return request(`/api/auth/change-password/${userId}`, {
    method: "POST",
    body: JSON.stringify({
      old_password: oldPassword,
      new_password: newPassword,
    }),
  });
}

export async function getUsers(): Promise<User[]> {
  return request<User[]>("/api/users");
}

export async function addUser(
  username: string,
  password: string,
  displayName: string,
  role: string
): Promise<{ id: number }> {
  return request("/api/users", {
    method: "POST",
    body: JSON.stringify({
      username,
      password,
      display_name: displayName,
      role,
    }),
  });
}

export async function deleteUser(userId: number): Promise<{ ok: boolean }> {
  return request(`/api/users/${userId}`, { method: "DELETE" });
}

// Stats
export async function getStats(): Promise<Stats> {
  return request<Stats>("/api/stats");
}

export async function getDistribution(
  col: string,
  limit?: number
): Promise<Distribution[]> {
  const params = new URLSearchParams({ col });
  if (limit) params.set("limit", String(limit));
  return request<Distribution[]>(
    `/api/stats/distribution/${col}?limit=${limit || 30}`
  );
}

// Persons
export async function getPersons(params: {
  search?: string;
  region?: string;
  haya?: string;
  mihna?: string;
  mukhtar_id?: number | null;
  deleted_filter?: string;
  limit?: number;
  offset?: number;
  include_family?: boolean;
}): Promise<PersonsResponse> {
  const sp = new URLSearchParams();
  if (params.search) sp.set("search", params.search);
  if (params.region) sp.set("region", params.region);
  if (params.haya) sp.set("haya", params.haya);
  if (params.mihna) sp.set("mihna", params.mihna);
  if (params.mukhtar_id) sp.set("mukhtar_id", String(params.mukhtar_id));
  if (params.deleted_filter) sp.set("deleted_filter", params.deleted_filter);
  if (params.limit) sp.set("limit", String(params.limit));
  if (params.offset) sp.set("offset", String(params.offset));
  if (params.include_family) sp.set("include_family", "true");
  return request<PersonsResponse>(`/api/persons?${sp.toString()}`);
}

export async function getPerson(id: number): Promise<Person> {
  return request<Person>(`/api/persons/${id}`);
}

export async function addPerson(
  data: Partial<Person>
): Promise<{ id: number }> {
  return request("/api/persons", {
    method: "POST",
    body: JSON.stringify({
      name: data.الاسم || "",
      birth: data.التولد || "",
      job: data.المهنة || "",
      qadha: data.القضاء || "",
      address: data.العنوان || "",
      mahal: data.المحل || "",
      phone: data.الهاتف || "",
      region: data.المنطقة || "",
      hay: data.الحي || "",
      mukhtar_id: data.mukhtar_id || null,
      marital_status: data.الحالة_الزوجية || "",
      sila: data.الصلة || "",
    }),
  });
}

export async function updatePerson(
  id: number,
  data: Partial<Person>
): Promise<{ ok: boolean }> {
  return request(`/api/persons/${id}`, {
    method: "PUT",
    body: JSON.stringify({
      name: data.الاسم || "",
      birth: data.التولد || "",
      job: data.المهنة || "",
      qadha: data.القضاء || "",
      address: data.العنوان || "",
      mahal: data.المحل || "",
      phone: data.الهاتف || "",
      region: data.المنطقة || "",
      hay: data.الحي || "",
      mukhtar_id: data.mukhtar_id || null,
      marital_status: data.الحالة_الزوجية || "",
      sila: data.الصلة || "",
    }),
  });
}

export async function deletePerson(id: number): Promise<{ ok: boolean }> {
  return request(`/api/persons/${id}`, { method: "DELETE" });
}

export async function restorePerson(id: number): Promise<{ ok: boolean }> {
  return request(`/api/persons/${id}/restore`, { method: "POST" });
}

// Family
export async function getPersonFamily(pid: number): Promise<Person[]> {
  return request<Person[]>(`/api/persons/${pid}/family`);
}

export async function createFamily(pid: number): Promise<{ family_id: number }> {
  return request(`/api/family/create/${pid}`, { method: "POST" });
}

export async function linkPersonToFamily(
  pid: number,
  familyId: number,
  relation: string
): Promise<{ ok: boolean }> {
  return request(`/api/family/link/${pid}`, {
    method: "POST",
    body: JSON.stringify({ family_id: familyId, relation }),
  });
}

export async function unlinkPersonFromFamily(
  pid: number
): Promise<{ ok: boolean }> {
  return request(`/api/family/unlink/${pid}`, { method: "POST" });
}

export async function searchFamilies(
  search: string
): Promise<FamilySearchResult[]> {
  return request<FamilySearchResult[]>(
    `/api/families/search?search=${encodeURIComponent(search)}`
  );
}

// Permanent delete
export async function permanentDeletePerson(
  pid: number
): Promise<{ ok: boolean }> {
  return request(`/api/persons/${pid}/permanent`, { method: "DELETE" });
}

// Mukhtars
export async function getMukhtars(): Promise<Mukhtar[]> {
  return request<Mukhtar[]>("/api/mukhtars");
}

export async function getMukhtarsGrouped(): Promise<
  Record<string, Mukhtar[]>
> {
  return request<Record<string, Mukhtar[]>>("/api/mukhtars/grouped");
}

export async function getMukhtar(id: number): Promise<Mukhtar> {
  return request<Mukhtar>(`/api/mukhtars/${id}`);
}

export async function addMukhtar(
  data: Partial<Mukhtar>
): Promise<{ id: number }> {
  return request("/api/mukhtars", {
    method: "POST",
    body: JSON.stringify({
      name: data.name || "",
      phone: data.phone || "",
      neighborhood_ids: data.neighborhood_ids || [],
    }),
  });
}

export async function updateMukhtar(
  id: number,
  data: Partial<Mukhtar>
): Promise<{ ok: boolean }> {
  return request(`/api/mukhtars/${id}`, {
    method: "PUT",
    body: JSON.stringify({
      name: data.name || "",
      phone: data.phone || "",
      neighborhood_ids: data.neighborhood_ids || [],
    }),
  });
}

export async function deleteMukhtar(id: number): Promise<{ ok: boolean }> {
  return request(`/api/mukhtars/${id}`, { method: "DELETE" });
}

// Neighborhoods
export async function getNeighborhoods(region?: string): Promise<Neighborhood[]> {
  const sp = region ? `?region=${encodeURIComponent(region)}` : "";
  return request<Neighborhood[]>(`/api/neighborhoods${sp}`);
}

export async function addNeighborhood(
  name: string,
  region: string
): Promise<{ id: number }> {
  return request("/api/neighborhoods", {
    method: "POST",
    body: JSON.stringify({ name, region }),
  });
}

export async function deleteNeighborhood(
  id: number
): Promise<{ ok: boolean }> {
  return request(`/api/neighborhoods/${id}`, { method: "DELETE" });
}

export async function getRegions(): Promise<string[]> {
  return request<string[]>("/api/regions");
}

export async function addRegion(name: string): Promise<{ id: number }> {
  return request(`/api/regions?name=${encodeURIComponent(name)}`, {
    method: "POST",
  });
}

export async function deleteRegion(id: number): Promise<{ ok: boolean }> {
  return request(`/api/regions/${id}`, { method: "DELETE" });
}

export async function getHayasForRegion(region: string): Promise<string[]> {
  return request<string[]>(`/api/hayas/${encodeURIComponent(region)}`);
}

// Backup
export async function getBackups(): Promise<Backup[]> {
  return request<Backup[]>("/api/backups");
}

export async function createBackup(): Promise<{ name: string }> {
  return request("/api/backups/create", { method: "POST" });
}

export async function restoreBackup(name: string): Promise<{ ok: boolean }> {
  return request(`/api/backups/restore?name=${encodeURIComponent(name)}`, {
    method: "POST",
  });
}

export async function deleteBackup(name: string): Promise<{ ok: boolean }> {
  return request(`/api/backups/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
}

// Lookup
export async function getMaritalStatuses(): Promise<string[]> {
  return request<string[]>("/api/lookup/marital-status");
}

export async function getFamilyRelations(): Promise<string[]> {
  return request<string[]>("/api/lookup/family-relations");
}

export async function getRoles(): Promise<string[]> {
  return request<string[]>("/api/lookup/roles");
}

// Export
export function getExportUrl(params: {
  search?: string;
  region?: string;
  haya?: string;
  mihna?: string;
  mukhtar_id?: number | null;
  deleted_filter?: string;
}): string {
  const sp = new URLSearchParams();
  if (params.search) sp.set("search", params.search);
  if (params.region) sp.set("region", params.region);
  if (params.haya) sp.set("haya", params.haya);
  if (params.mihna) sp.set("mihna", params.mihna);
  if (params.mukhtar_id) sp.set("mukhtar_id", String(params.mukhtar_id));
  if (params.deleted_filter) sp.set("deleted_filter", params.deleted_filter);
  return `${BASE_URL}/api/persons/export/excel?${sp.toString()}`;
}

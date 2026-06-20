export interface Person {
  id: number;
  الاسم: string;
  التولد: string;
  المهنة: string;
  القضاء: string;
  العنوان: string;
  المحل: string;
  الهاتف: string;
  المنطقة: string;
  الحي: string;
  mukhtar_id: number | null;
  الحالة_الزوجية: string;
  الصلة: string;
  الشيت: string;
  is_deleted: number;
  family_id: number | null;
  الملاحظات?: string;
  mukhtar_name?: string;
  matched_by_search?: boolean;
  included_as_family?: boolean;
}

export interface Region {
  id: number;
  name: string;
  created_at?: string;
}

export interface FamilySearchResult {
  family_id: number;
  head_name: string;
  members_count: number;
  region: string;
  hay: string;
}

export interface PersonWithFamily extends Person {
  family_members: Person[];
}

export interface Mukhtar {
  id: number;
  name: string;
  phone: string;
  neighborhood_ids?: number[];
  neighborhood_names?: string[];
  region?: string;
  created_at?: string;
}

export interface Neighborhood {
  id: number;
  name: string;
  region: string;
}

export interface Stats {
  total: number;
  active: number;
  deleted: number;
  with_full_name: number;
  mukhtars: number;
  neighborhoods: number;
  unique_jobs: number;
}

export interface User {
  id: number;
  username: string;
  display_name: string;
  role: string;
}

export interface Backup {
  name: string;
  size_mb: number;
  date: string;
}

export interface Distribution {
  value: string;
  count: number;
}

export interface PersonsResponse {
  rows: Person[];
  total: number;
}

export interface LoginResponse {
  user: User;
}

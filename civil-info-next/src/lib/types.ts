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
  deleted: number;
  family_id: number | null;
  mukhtar_name?: string;
}

export interface Mukhtar {
  id: number;
  name: string;
  phone: string;
  neighborhood_ids?: number[];
  neighborhoods?: string[];
  region?: string;
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

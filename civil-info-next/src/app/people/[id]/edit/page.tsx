"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import {
  getPerson,
  updatePerson,
  getRegions,
  getMukhtars,
  getMaritalStatuses,
  getFamilyRelations,
  getHayasForRegion,
} from "@/lib/api";
import type { Person, Mukhtar } from "@/lib/types";

export default function EditPersonPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [form, setForm] = useState<Partial<Person>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [regions, setRegions] = useState<string[]>([]);
  const [mukhtars, setMukhtars] = useState<Mukhtar[]>([]);
  const [maritalStatuses, setMaritalStatuses] = useState<string[]>([]);
  const [familyRelations, setFamilyRelations] = useState<string[]>([]);
  const [hayas, setHayas] = useState<string[]>([]);

  useEffect(() => {
    Promise.all([
      getPerson(id),
      getRegions(),
      getMukhtars(),
      getMaritalStatuses(),
      getFamilyRelations(),
    ])
      .then(([person, regs, muks, ms, fr]) => {
        setForm(person);
        setRegions(regs);
        setMukhtars(muks);
        setMaritalStatuses(ms);
        setFamilyRelations(fr);
        if (person.المنطقة) {
          getHayasForRegion(person.المنطقة)
            .then(setHayas)
            .catch(() => {});
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleRegionChange = (val: string) => {
    setForm((prev) => ({ ...prev, المنطقة: val, الحي: "" }));
    if (val) {
      getHayasForRegion(val)
        .then(setHayas)
        .catch(() => setHayas([]));
    } else {
      setHayas([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);
    try {
      await updatePerson(id, form);
      setSuccess("تم تحديث البيانات بنجاح");
      setTimeout(() => router.push(`/people/${id}`), 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في الحفظ");
    } finally {
      setSaving(false);
    }
  };

  const updateField = (key: string, value: string | number | null) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <AppShell title="تعديل بيانات الشخص">
      {loading ? (
        <div style={{ textAlign: "center", padding: 60 }}>
          <div className="spinner spinner-dark" />
        </div>
      ) : (
        <div className="card">
          <div style={{ marginBottom: 20, display: "flex", gap: 12 }}>
            <button
              onClick={() => router.back()}
              className="btn btn-outline"
            >
              رجوع
            </button>
            <h2 style={{ margin: 0, color: "var(--navy)" }}>
              تعديل: {form.الاسم}
            </h2>
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>الاسم</label>
                <input
                  className="form-input"
                  value={form.الاسم || ""}
                  onChange={(e) => updateField("الاسم", e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>التولد</label>
                <input
                  className="form-input"
                  value={form.التولد || ""}
                  onChange={(e) => updateField("التولد", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>المهنة</label>
                <input
                  className="form-input"
                  value={form.المهنة || ""}
                  onChange={(e) => updateField("المهنة", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>القضاء</label>
                <input
                  className="form-input"
                  value={form.القضاء || ""}
                  onChange={(e) => updateField("القضاء", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>العنوان</label>
                <input
                  className="form-input"
                  value={form.العنوان || ""}
                  onChange={(e) => updateField("العنوان", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>المحل</label>
                <input
                  className="form-input"
                  value={form.المحل || ""}
                  onChange={(e) => updateField("المحل", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>الهاتف</label>
                <input
                  className="form-input"
                  value={form.الهاتف || ""}
                  onChange={(e) => updateField("الهاتف", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>المنطقة</label>
                <select
                  className="form-input"
                  value={form.المنطقة || ""}
                  onChange={(e) => handleRegionChange(e.target.value)}
                >
                  <option value="">اختر المنطقة</option>
                  {regions.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>الحي</label>
                <select
                  className="form-input"
                  value={form.الحي || ""}
                  onChange={(e) => updateField("الحي", e.target.value)}
                >
                  <option value="">اختر الحي</option>
                  {hayas.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>المختار</label>
                <select
                  className="form-input"
                  value={form.mukhtar_id || ""}
                  onChange={(e) =>
                    updateField(
                      "mukhtar_id",
                      e.target.value ? Number(e.target.value) : null
                    )
                  }
                >
                  <option value="">بدون مختار</option>
                  {mukhtars.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>الحالة الزوجية</label>
                <select
                  className="form-input"
                  value={form.الحالة_الزوجية || ""}
                  onChange={(e) =>
                    updateField("الحالة_الزوجية", e.target.value)
                  }
                >
                  <option value="">اختر</option>
                  {maritalStatuses.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>الصلة</label>
                <input
                  className="form-input"
                  value={form.الصلة || ""}
                  onChange={(e) => updateField("الصلة", e.target.value)}
                />
              </div>
            </div>

            <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={saving}
              >
                {saving ? <span className="spinner" /> : "حفظ التعديلات"}
              </button>
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => router.back()}
              >
                إلغاء
              </button>
            </div>
          </form>
        </div>
      )}
    </AppShell>
  );
}

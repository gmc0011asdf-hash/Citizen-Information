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
  getNeighborhoods,
} from "@/lib/api";
import { can } from "@/lib/auth";
import type { Person, Mukhtar, Neighborhood } from "@/lib/types";

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
  const [hayas, setHayas] = useState<Neighborhood[]>([]);
  const [duplicates, setDuplicates] = useState<any[]>([]);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);

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
          getNeighborhoods(person.المنطقة)
            .then(setHayas)
            .catch(() => {});
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleRegionChange = (val: string) => {
    setForm((prev) => ({ ...prev, المنطقة: val, الحي: "", mukhtar_id: null }));
    if (val) {
      getNeighborhoods(val)
        .then(setHayas)
        .catch(() => setHayas([]));
    } else {
      setHayas([]);
    }
  };

  const filteredMukhtars = form.المنطقة
    ? mukhtars.filter((m) => m.region === form.المنطقة || !m.region)
    : mukhtars;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);
    try {
      await updatePerson(id, form);
      setSuccess("تم تحديث البيانات بنجاح");
      setTimeout(() => router.push(`/people/${id}`), 1000);
    } catch (err: any) {
      if (err.status === 409 && err.matches) {
        setDuplicates(err.matches);
        setShowDuplicateModal(true);
      } else {
        setError(err instanceof Error ? err.message : "خطأ في الحفظ");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleForceSave = async () => {
    try {
      await updatePerson(id, form, true);
      setSuccess("تم تحديث البيانات بنجاح");
      setTimeout(() => router.push(`/people/${id}`), 1000);
    } catch (err: any) {
      setError(err.message);
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
                  disabled={!form.المنطقة}
                >
                  <option value="">{form.المنطقة ? "اختر الحي" : "اختر المنطقة أولاً"}</option>
                  {hayas.map((h) => (
                    <option key={h.id} value={h.name}>
                      {h.name}
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
                  {filteredMukhtars.map((m) => (
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
                <select
                  className="form-input"
                  value={form.الصلة || ""}
                  onChange={(e) => updateField("الصلة", e.target.value)}
                >
                  <option value="">اختر</option>
                  {familyRelations.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ gridColumn: "1 / -1" }}>
                <label>الملاحظات</label>
                <textarea
                  className="form-input"
                  rows={3}
                  placeholder="ملاحظات إضافية..."
                  value={form.الملاحظات || ""}
                  onChange={(e) => setForm({ ...form, الملاحظات: e.target.value })}
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
      {showDuplicateModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div className="card" style={{ maxWidth: 600, maxHeight: "80vh", overflow: "auto" }}>
            <h3 style={{ color: "#dc2626", marginBottom: 16 }}>&#9888;&#65039; يوجد اسم مشابه في النظام</h3>
            <p style={{ marginBottom: 12 }}>تم العثور على سجلات مشابهة. يرجى المراجعة قبل الحفظ:</p>
            <table className="data-table">
              <thead>
                <tr>
                  <th>التسلسل</th>
                  <th>الاسم</th>
                  <th>رقم الأسرة</th>
                  <th>المنطقة</th>
                  <th>الهاتف</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {duplicates.map((d) => (
                  <tr key={d.id}>
                    <td>{d.id}</td>
                    <td style={{ fontWeight: 600 }}>{d.name}</td>
                    <td>{d.family_id || "—"}</td>
                    <td>{d.region || "—"}</td>
                    <td style={{ direction: "ltr", textAlign: "right" }}>{d.phone || "—"}</td>
                    <td>
                      <a href={`/people/${d.id}`} className="btn btn-sm btn-outline">فتح السجل</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ display: "flex", gap: 8, marginTop: 16, justifyContent: "flex-start" }}>
              <button onClick={() => setShowDuplicateModal(false)} className="btn btn-outline">إلغاء</button>
              {can("hard_delete") && (
                <button onClick={handleForceSave} className="btn btn-danger">حفظ رغم التشابه (مدير فقط)</button>
              )}
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import {
  getPerson,
  deletePerson,
  restorePerson,
  getPersonFamily,
  createFamily,
  linkPersonToFamily,
  unlinkPersonFromFamily,
  searchFamilies,
  getFamilyRelations,
} from "@/lib/api";
import type { Person, FamilySearchResult } from "@/lib/types";

export default function PersonDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [person, setPerson] = useState<Person | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  // Family state
  const [familyMembers, setFamilyMembers] = useState<Person[]>([]);
  const [familyLoading, setFamilyLoading] = useState(false);
  const [showLinkForm, setShowLinkForm] = useState(false);
  const [familySearch, setFamilySearch] = useState("");
  const [familyResults, setFamilyResults] = useState<FamilySearchResult[]>([]);
  const [familySearching, setFamilySearching] = useState(false);
  const [linkRelation, setLinkRelation] = useState("");
  const [familyRelations, setFamilyRelations] = useState<string[]>([]);

  const loadFamily = () => {
    setFamilyLoading(true);
    getPersonFamily(id)
      .then(setFamilyMembers)
      .catch(() => setFamilyMembers([]))
      .finally(() => setFamilyLoading(false));
  };

  useEffect(() => {
    setLoading(true);
    getPerson(id)
      .then((p) => {
        setPerson(p);
        if (p.family_id) {
          setFamilyLoading(true);
          getPersonFamily(id)
            .then(setFamilyMembers)
            .catch(() => setFamilyMembers([]))
            .finally(() => setFamilyLoading(false));
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
    getFamilyRelations()
      .then(setFamilyRelations)
      .catch(() => {});
  }, [id]);

  const handleDelete = async () => {
    if (!confirm("هل أنت متأكد من حذف هذا السجل؟")) return;
    setActionLoading(true);
    try {
      await deletePerson(id);
      router.push("/people");
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في الحذف");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRestore = async () => {
    setActionLoading(true);
    try {
      await restorePerson(id);
      setPerson((prev) => (prev ? { ...prev, deleted: 0 } : prev));
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في الاستعادة");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateFamily = async () => {
    setActionLoading(true);
    try {
      const res = await createFamily(id);
      setPerson((prev) =>
        prev ? { ...prev, family_id: res.family_id } : prev
      );
      loadFamily();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في إنشاء الأسرة");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSearchFamilies = async () => {
    if (!familySearch.trim()) return;
    setFamilySearching(true);
    try {
      const results = await searchFamilies(familySearch);
      setFamilyResults(results);
    } catch {
      setFamilyResults([]);
    } finally {
      setFamilySearching(false);
    }
  };

  const handleLinkToFamily = async (familyId: number) => {
    if (!linkRelation) {
      setError("يرجى اختيار الصلة");
      return;
    }
    setActionLoading(true);
    try {
      await linkPersonToFamily(id, familyId, linkRelation);
      setPerson((prev) =>
        prev ? { ...prev, family_id: familyId, الصلة: linkRelation } : prev
      );
      setShowLinkForm(false);
      setFamilySearch("");
      setFamilyResults([]);
      setLinkRelation("");
      loadFamily();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في الربط");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUnlinkFromFamily = async () => {
    if (!confirm("هل أنت متأكد من فصل هذا الشخص عن الأسرة؟")) return;
    setActionLoading(true);
    try {
      await unlinkPersonFromFamily(id);
      setPerson((prev) =>
        prev ? { ...prev, family_id: null } : prev
      );
      setFamilyMembers([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في الفصل");
    } finally {
      setActionLoading(false);
    }
  };

  const fields: { label: string; key: keyof Person }[] = [
    { label: "الاسم", key: "الاسم" },
    { label: "التولد", key: "التولد" },
    { label: "المهنة", key: "المهنة" },
    { label: "القضاء", key: "القضاء" },
    { label: "العنوان", key: "العنوان" },
    { label: "المحل", key: "المحل" },
    { label: "الهاتف", key: "الهاتف" },
    { label: "المنطقة", key: "المنطقة" },
    { label: "الحي", key: "الحي" },
    { label: "الحالة الزوجية", key: "الحالة_الزوجية" },
    { label: "الصلة", key: "الصلة" },
    { label: "المختار", key: "mukhtar_name" },
    { label: "الملاحظات", key: "الملاحظات" },
  ];

  return (
    <AppShell title="تفاصيل الشخص">
      {loading ? (
        <div style={{ textAlign: "center", padding: 60 }}>
          <div className="spinner spinner-dark" />
        </div>
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : person ? (
        <>
          <div className="card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 24,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <button
                  onClick={() => router.back()}
                  className="btn btn-outline"
                >
                  رجوع
                </button>
                <h2 style={{ margin: 0, color: "var(--navy)" }}>
                  {person.الاسم}
                </h2>
                <span
                  className={`badge ${person.deleted ? "badge-deleted" : "badge-active"}`}
                >
                  {person.deleted ? "محذوف" : "نشط"}
                </span>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <Link
                  href={`/people/${id}/edit`}
                  className="btn btn-primary"
                >
                  تعديل
                </Link>
                {person.deleted ? (
                  <button
                    onClick={handleRestore}
                    className="btn btn-success"
                    disabled={actionLoading}
                  >
                    استعادة
                  </button>
                ) : (
                  <button
                    onClick={handleDelete}
                    className="btn btn-danger"
                    disabled={actionLoading}
                  >
                    حذف
                  </button>
                )}
              </div>
            </div>

            <div className="detail-grid">
              {fields.map((f) => (
                <div key={f.key} className="detail-item">
                  <div className="detail-label">{f.label}</div>
                  <div className="detail-value">
                    {String(person[f.key] ?? "-") || "-"}
                  </div>
                </div>
              ))}
              {person.family_id && (
                <div className="detail-item">
                  <div className="detail-label">رقم الأسرة</div>
                  <div className="detail-value">{person.family_id}</div>
                </div>
              )}
              <div className="detail-item">
                <div className="detail-label">التسلسل</div>
                <div className="detail-value">{person.id}</div>
              </div>
              <div className="detail-item">
                <div className="detail-label">الشيت</div>
                <div className="detail-value">{person.الشيت || "-"}</div>
              </div>
            </div>
          </div>

          {/* Family Section */}
          <div className="card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 16,
              }}
            >
              <h3 style={{ margin: 0, color: "var(--navy)" }}>
                الأسرة
                {person.family_id && (
                  <span style={{
                    marginRight: 10,
                    fontSize: 14,
                    background: "#dbeafe",
                    color: "#1e40af",
                    padding: "4px 12px",
                    borderRadius: 12,
                    fontWeight: 600,
                  }}>
                    رقم الأسرة: {person.family_id}
                  </span>
                )}
              </h3>
              {person.family_id && (
                <button
                  onClick={handleUnlinkFromFamily}
                  className="btn btn-sm btn-outline"
                  disabled={actionLoading}
                  style={{ color: "#dc2626", borderColor: "#dc2626" }}
                >
                  فصل عن الأسرة
                </button>
              )}
            </div>

            {person.family_id ? (
              familyLoading ? (
                <div style={{ textAlign: "center", padding: 20 }}>
                  <div className="spinner spinner-dark" />
                </div>
              ) : !Array.isArray(familyMembers) || familyMembers.length === 0 ? (
                <div className="empty-state" style={{ padding: 20 }}>
                  <p>لا يوجد أفراد آخرون في الأسرة</p>
                </div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>الاسم</th>
                        <th>الصلة</th>
                        <th>الهاتف</th>
                        <th>إجراءات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {familyMembers.map((m, i) => (
                        <tr
                          key={m.id}
                          style={
                            m.id === id
                              ? { background: "#eff6ff" }
                              : undefined
                          }
                        >
                          <td>{i + 1}</td>
                          <td>
                            <strong>
                              {m.الاسم}
                              {m.id === id && " (أنت)"}
                            </strong>
                          </td>
                          <td>{m.الصلة || "-"}</td>
                          <td
                            style={{
                              direction: "ltr",
                              textAlign: "right",
                            }}
                          >
                            {m.الهاتف || "-"}
                          </td>
                          <td>
                            {m.id !== id && (
                              <Link
                                href={`/people/${m.id}`}
                                className="btn btn-sm btn-outline"
                              >
                                عرض
                              </Link>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            ) : (
              <div>
                <p style={{ color: "#64748b", marginBottom: 16 }}>
                  هذا الشخص غير مرتبط بأسرة
                </p>
                <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                  <button
                    onClick={handleCreateFamily}
                    className="btn btn-primary"
                    disabled={actionLoading}
                  >
                    إنشاء أسرة جديدة
                  </button>
                  <button
                    onClick={() => setShowLinkForm(!showLinkForm)}
                    className="btn btn-gold"
                  >
                    ربط بأسرة موجودة
                  </button>
                </div>

                {showLinkForm && (
                  <div
                    style={{
                      padding: 16,
                      background: "#f8fafc",
                      borderRadius: 8,
                      border: "1px solid #e2e8f0",
                    }}
                  >
                    <div className="form-group">
                      <label>الصلة</label>
                      <select
                        className="form-input"
                        value={linkRelation}
                        onChange={(e) => setLinkRelation(e.target.value)}
                      >
                        <option value="">اختر الصلة</option>
                        {familyRelations.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>بحث عن أسرة</label>
                      <div style={{ display: "flex", gap: 8 }}>
                        <input
                          className="form-input"
                          placeholder="ابحث باسم رب الأسرة..."
                          value={familySearch}
                          onChange={(e) => setFamilySearch(e.target.value)}
                          onKeyDown={(e) =>
                            e.key === "Enter" && handleSearchFamilies()
                          }
                        />
                        <button
                          onClick={handleSearchFamilies}
                          className="btn btn-primary"
                          disabled={familySearching}
                        >
                          {familySearching ? (
                            <span className="spinner" />
                          ) : (
                            "بحث"
                          )}
                        </button>
                      </div>
                    </div>

                    {familyResults.length > 0 && (
                      <div style={{ overflowX: "auto" }}>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>رقم الأسرة</th>
                              <th>رب الأسرة</th>
                              <th>عدد الأفراد</th>
                              <th>المنطقة</th>
                              <th>الحي</th>
                              <th>إجراءات</th>
                            </tr>
                          </thead>
                          <tbody>
                            {familyResults.map((f) => (
                              <tr key={f.family_id}>
                                <td>{f.family_id}</td>
                                <td>{f.head_name}</td>
                                <td>{f.members_count}</td>
                                <td>{f.region || "-"}</td>
                                <td>{f.hay || "-"}</td>
                                <td>
                                  <button
                                    onClick={() =>
                                      handleLinkToFamily(f.family_id)
                                    }
                                    className="btn btn-sm btn-success"
                                    disabled={actionLoading}
                                  >
                                    ربط
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      ) : null}
    </AppShell>
  );
}

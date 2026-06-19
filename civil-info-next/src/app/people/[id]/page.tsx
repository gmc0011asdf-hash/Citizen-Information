"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { getPerson, deletePerson, restorePerson } from "@/lib/api";
import type { Person } from "@/lib/types";

export default function PersonDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [person, setPerson] = useState<Person | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getPerson(id)
      .then(setPerson)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
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
      ) : null}
    </AppShell>
  );
}

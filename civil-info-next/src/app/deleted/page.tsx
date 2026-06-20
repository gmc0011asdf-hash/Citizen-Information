"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { can } from "@/lib/auth";
import { getPersons, restorePerson, permanentDeletePerson } from "@/lib/api";
import type { Person } from "@/lib/types";

export default function DeletedPage() {
  const [persons, setPersons] = useState<Person[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(50);

  // Permanent delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<Person | null>(null);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const storedPerPage = localStorage.getItem("perPage");
    if (storedPerPage) setPerPage(Number(storedPerPage));

    const handlePerPageChange = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      setPerPage(detail);
      setPage(1);
    };
    window.addEventListener("perPageChanged", handlePerPageChange);
    return () =>
      window.removeEventListener("perPageChanged", handlePerPageChange);
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getPersons({
        search,
        deleted_filter: "deleted",
        limit: perPage,
        offset: (page - 1) * perPage,
      });
      setPersons(res.rows);
      setTotal(res.total);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [search, page, perPage]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRestore = async (id: number) => {
    try {
      await restorePerson(id);
      fetchData();
    } catch {
      /* ignore */
    }
  };

  const handlePermanentDelete = async () => {
    if (!deleteTarget || deleteConfirmText !== "حذف") return;
    setDeleting(true);
    try {
      await permanentDeletePerson(deleteTarget.id);
      setDeleteTarget(null);
      setDeleteConfirmText("");
      fetchData();
    } catch {
      /* ignore */
    } finally {
      setDeleting(false);
    }
  };

  const totalPages = Math.ceil(total / perPage);

  return (
    <AppShell title="المحذوفات">
      <div className="card">
        <div className="filters-bar">
          <div className="form-group" style={{ flex: 2 }}>
            <label>بحث</label>
            <input
              className="form-input"
              placeholder="ابحث بالاسم..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </div>

        <div style={{ marginBottom: 16, fontSize: 14, color: "#64748b" }}>
          إجمالي المحذوفات: <strong>{total}</strong>
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: 40 }}>
            <div className="spinner spinner-dark" />
          </div>
        ) : persons.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🗑️</div>
            <p>لا توجد سجلات محذوفة</p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>الاسم</th>
                  <th>المهنة</th>
                  <th>المنطقة</th>
                  <th>الهاتف</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {persons.map((p, i) => (
                  <tr key={p.id}>
                    <td>{(page - 1) * perPage + i + 1}</td>
                    <td>
                      <Link
                        href={`/people/${p.id}`}
                        style={{
                          color: "var(--navy)",
                          fontWeight: 600,
                          textDecoration: "none",
                        }}
                      >
                        {p.الاسم}
                      </Link>
                    </td>
                    <td>{p.المهنة || "-"}</td>
                    <td>{p.المنطقة || "-"}</td>
                    <td style={{ direction: "ltr", textAlign: "right" }}>
                      {p.الهاتف || "-"}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 4 }}>
                        {can("restore") && (
                          <button
                            onClick={() => handleRestore(p.id)}
                            className="btn btn-sm btn-success"
                          >
                            استعادة
                          </button>
                        )}
                        {can("hard_delete") && (
                          <button
                            onClick={() => setDeleteTarget(p)}
                            className="btn btn-sm btn-danger"
                          >
                            حذف نهائي
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="pagination">
            <button disabled={page <= 1} onClick={() => setPage(1)}>
              الأولى
            </button>
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
              السابق
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (page <= 3) {
                pageNum = i + 1;
              } else if (page >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = page - 2 + i;
              }
              return (
                <button
                  key={pageNum}
                  className={page === pageNum ? "active" : ""}
                  onClick={() => setPage(pageNum)}
                >
                  {pageNum}
                </button>
              );
            })}
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
            >
              التالي
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(totalPages)}
            >
              الأخيرة
            </button>
          </div>
        )}
      </div>

      {/* Permanent Delete Confirmation Dialog */}
      {deleteTarget && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
          }}
          onClick={() => {
            setDeleteTarget(null);
            setDeleteConfirmText("");
          }}
        >
          <div
            style={{
              background: "white",
              borderRadius: 12,
              padding: 32,
              maxWidth: 450,
              width: "90%",
              boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              style={{
                margin: "0 0 12px",
                color: "#dc2626",
                fontSize: 18,
              }}
            >
              تأكيد الحذف النهائي
            </h3>
            <p style={{ color: "#64748b", fontSize: 14, marginBottom: 8 }}>
              الشخص: <strong style={{ color: "#111827" }}>{deleteTarget.الاسم}</strong>
            </p>
            <div
              style={{
                background: "#fef2f2",
                border: "1px solid #fecaca",
                borderRadius: 8,
                padding: 12,
                marginBottom: 16,
                fontSize: 13,
                color: "#991b1b",
              }}
            >
              هذا الإجراء سيحذف السجل نهائيا من قاعدة البيانات ولا يمكن
              استعادته
            </div>
            <div className="form-group" style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 13, color: "#64748b" }}>
                اكتب &quot;حذف&quot; للتأكيد
              </label>
              <input
                className="form-input"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder='اكتب "حذف" هنا'
                autoFocus
              />
            </div>
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button
                onClick={() => {
                  setDeleteTarget(null);
                  setDeleteConfirmText("");
                }}
                className="btn btn-outline"
              >
                إلغاء
              </button>
              <button
                onClick={handlePermanentDelete}
                className="btn btn-danger"
                disabled={deleteConfirmText !== "حذف" || deleting}
              >
                {deleting ? <span className="spinner" /> : "حذف نهائي"}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

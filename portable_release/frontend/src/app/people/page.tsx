"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { can } from "@/lib/auth";
import { getPersons, getRegions, getMukhtars, getExportUrl } from "@/lib/api";
import type { Person, Mukhtar } from "@/lib/types";

export default function PeoplePage() {
  const [persons, setPersons] = useState<Person[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [region, setRegion] = useState("");
  const [hay, setHay] = useState("");
  const [job, setJob] = useState("");
  const [mukhtarId, setMukhtarId] = useState<number | null>(null);
  const [status, setStatus] = useState("active");
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(50);
  const [regions, setRegions] = useState<string[]>([]);
  const [mukhtars, setMukhtars] = useState<Mukhtar[]>([]);
  const [userRole, setUserRole] = useState<string>("");

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        const u = JSON.parse(storedUser);
        setUserRole(u.role || "");
      } catch { /* ignore */ }
    }

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

  useEffect(() => {
    getRegions()
      .then(setRegions)
      .catch(() => {});
    getMukhtars()
      .then(setMukhtars)
      .catch(() => {});
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getPersons({
        search,
        region,
        haya: hay,
        mihna: job,
        mukhtar_id: mukhtarId,
        deleted_filter: status,
        limit: perPage,
        offset: (page - 1) * perPage,
        include_family: !!search,
      });
      setPersons(res.rows);
      setTotal(res.total);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [search, region, hay, job, mukhtarId, status, page, perPage]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalPages = Math.ceil(total / perPage);

  const handleSearch = () => {
    setPage(1);
    fetchData();
  };

  const handleExport = () => {
    const url = getExportUrl({
      search,
      region,
      haya: hay,
      mihna: job,
      mukhtar_id: mukhtarId,
      deleted_filter: status,
    });
    window.open(url, "_blank");
  };

  return (
    <AppShell title="قائمة الأشخاص">
      <div className="card">
        <div className="filters-bar">
          <div className="form-group" style={{ flex: 2 }}>
            <label>بحث</label>
            <input
              className="form-input"
              placeholder="ابحث بالاسم أو الهاتف..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          <div className="form-group">
            <label>المنطقة</label>
            <select
              className="form-input"
              value={region}
              onChange={(e) => {
                setRegion(e.target.value);
                setPage(1);
              }}
            >
              <option value="">الكل</option>
              {regions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>الحي</label>
            <input
              className="form-input"
              placeholder="الحي"
              value={hay}
              onChange={(e) => setHay(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>المهنة</label>
            <input
              className="form-input"
              placeholder="المهنة"
              value={job}
              onChange={(e) => setJob(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>المختار</label>
            <select
              className="form-input"
              value={mukhtarId || ""}
              onChange={(e) => {
                setMukhtarId(e.target.value ? Number(e.target.value) : null);
                setPage(1);
              }}
            >
              <option value="">الكل</option>
              {mukhtars.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>الحالة</label>
            <select
              className="form-input"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
            >
              <option value="active">النشطة</option>
              <option value="deleted">المحذوفة</option>
              <option value="all">الكل</option>
            </select>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 16,
          }}
        >
          <div style={{ fontSize: 14, color: "#64748b" }}>
            إجمالي النتائج: <strong>{total}</strong>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {can("create") && (
              <Link href="/people/new" className="btn btn-primary">
                إضافة شخص
              </Link>
            )}
            <button onClick={handleExport} className="btn btn-gold">
              تصدير Excel
            </button>
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: 40 }}>
            <div className="spinner spinner-dark" />
          </div>
        ) : persons.length === 0 ? (
          <div className="empty-state">
            <div className="icon">📭</div>
            <p>لا توجد نتائج</p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>الاسم</th>
                  <th>الحالة</th>
                  <th>رقم الأسرة</th>
                  <th>المهنة</th>
                  <th>المنطقة</th>
                  <th>الهاتف</th>
                  <th>الملاحظات</th>
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
                      {p.included_as_family && (
                        <span
                          style={{
                            marginRight: 6,
                            fontSize: 11,
                            background: "#dbeafe",
                            color: "#1e40af",
                            padding: "2px 8px",
                            borderRadius: 12,
                            fontWeight: 600,
                          }}
                        >
                          من نفس الأسرة
                        </span>
                      )}
                      {p.matched_by_search && (
                        <span
                          style={{
                            marginRight: 6,
                            fontSize: 11,
                            background: "#dcfce7",
                            color: "#166534",
                            padding: "2px 8px",
                            borderRadius: 12,
                            fontWeight: 600,
                          }}
                        >
                          نتيجة مطابقة
                        </span>
                      )}
                    </td>
                    <td>
                      <span
                        className={`badge ${p.is_deleted ? "badge-deleted" : "badge-active"}`}
                      >
                        {p.is_deleted ? "محذوف" : "نشط"}
                      </span>
                    </td>
                    <td>
                      {p.family_id ? (
                        <span style={{
                          background: "#dbeafe", color: "#1e40af", padding: "2px 10px",
                          borderRadius: 12, fontWeight: 700, fontSize: 12,
                        }}>
                          {p.family_id}
                        </span>
                      ) : "—"}
                    </td>
                    <td>{p.المهنة || "-"}</td>
                    <td>{p.المنطقة || "-"}</td>
                    <td style={{ direction: "ltr", textAlign: "right" }}>
                      {p.الهاتف || "-"}
                    </td>
                    <td>
                      {p.الملاحظات
                        ? p.الملاحظات.length > 30
                          ? p.الملاحظات.substring(0, 30) + "..."
                          : p.الملاحظات
                        : "-"}
                    </td>
                    <td>
                      <Link
                        href={`/people/${p.id}`}
                        className="btn btn-sm btn-outline"
                      >
                        عرض
                      </Link>
                      {can("edit") && (
                        <Link href={`/people/${p.id}/edit`} className="btn btn-sm btn-primary" style={{ marginRight: 4 }}>
                          تعديل
                        </Link>
                      )}
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
    </AppShell>
  );
}

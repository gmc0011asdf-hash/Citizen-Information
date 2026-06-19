"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  getMukhtarsGrouped,
  addMukhtar,
  updateMukhtar,
  deleteMukhtar,
  getNeighborhoods,
  getRegions,
} from "@/lib/api";
import type { Mukhtar, Neighborhood } from "@/lib/types";

type TabType = "علي الغربي" | "علي الشرقي" | "الكل" | "إضافة";

export default function MukhtarsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("الكل");
  const [grouped, setGrouped] = useState<Record<string, Mukhtar[]>>({});
  const [loading, setLoading] = useState(true);
  const [neighborhoods, setNeighborhoods] = useState<Neighborhood[]>([]);
  const [regions, setRegions] = useState<string[]>([]);

  // Add form
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newRegion, setNewRegion] = useState("");
  const [newNeighborhoodIds, setNewNeighborhoodIds] = useState<number[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Edit
  const [editId, setEditId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editRegion, setEditRegion] = useState("");
  const [editNeighborhoodIds, setEditNeighborhoodIds] = useState<number[]>([]);

  const fetchData = () => {
    setLoading(true);
    Promise.all([getMukhtarsGrouped(), getNeighborhoods(), getRegions()])
      .then(([g, n, r]) => {
        setGrouped(g);
        setNeighborhoods(n);
        setRegions(r);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const allMukhtars = Object.values(grouped).flat();

  const getDisplayedMukhtars = (): Mukhtar[] => {
    if (activeTab === "الكل") return allMukhtars;
    if (activeTab === "إضافة") return [];
    return grouped[activeTab] || [];
  };

  // Filter neighborhoods by selected region for add form
  const addFilteredNeighborhoods = newRegion
    ? neighborhoods.filter((n) => n.region === newRegion)
    : neighborhoods;

  // Filter neighborhoods by selected region for edit form
  const editFilteredNeighborhoods = editRegion
    ? neighborhoods.filter((n) => n.region === editRegion)
    : neighborhoods;

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!newName.trim()) {
      setError("اسم المختار مطلوب");
      return;
    }
    setSaving(true);
    try {
      await addMukhtar({
        name: newName,
        phone: newPhone,
        neighborhood_ids: newNeighborhoodIds,
        region: newRegion,
      });
      setSuccess("تم إضافة المختار بنجاح");
      setNewName("");
      setNewPhone("");
      setNewRegion("");
      setNewNeighborhoodIds([]);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في الإضافة");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("هل أنت متأكد من حذف هذا المختار؟")) return;
    try {
      await deleteMukhtar(id);
      fetchData();
    } catch {
      /* ignore */
    }
  };

  const startEdit = (m: Mukhtar) => {
    setEditId(m.id);
    setEditName(m.name);
    setEditPhone(m.phone || "");
    setEditRegion(m.region || "");
    setEditNeighborhoodIds(m.neighborhood_ids || []);
  };

  const handleUpdate = async () => {
    if (!editId) return;
    setError("");
    try {
      await updateMukhtar(editId, {
        name: editName,
        phone: editPhone,
        neighborhood_ids: editNeighborhoodIds,
        region: editRegion,
      });
      setEditId(null);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في التعديل");
    }
  };

  const toggleNeighborhood = (
    nid: number,
    selected: number[],
    setter: (ids: number[]) => void
  ) => {
    if (selected.includes(nid)) {
      setter(selected.filter((x) => x !== nid));
    } else {
      setter([...selected, nid]);
    }
  };

  const tabs: TabType[] = ["علي الغربي", "علي الشرقي", "الكل", "إضافة"];

  return (
    <AppShell title="المختارون">
      <div className="card">
        <div className="tabs">
          {tabs.map((t) => (
            <button
              key={t}
              className={`tab ${activeTab === t ? "active" : ""}`}
              onClick={() => setActiveTab(t)}
            >
              {t}
            </button>
          ))}
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {activeTab === "إضافة" ? (
          <form onSubmit={handleAdd}>
            <div className="form-grid">
              <div className="form-group">
                <label>اسم المختار *</label>
                <input
                  className="form-input"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>رقم الهاتف</label>
                <input
                  className="form-input"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>المنطقة</label>
                <select
                  className="form-input"
                  value={newRegion}
                  onChange={(e) => {
                    setNewRegion(e.target.value);
                    setNewNeighborhoodIds([]);
                  }}
                >
                  <option value="">اختر المنطقة</option>
                  {regions.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>الأحياء التابعة {newRegion && `(${newRegion})`}</label>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 8,
                  maxHeight: 200,
                  overflowY: "auto",
                  padding: 8,
                  border: "1px solid #e2e8f0",
                  borderRadius: 8,
                }}
              >
                {addFilteredNeighborhoods.length === 0 ? (
                  <span style={{ color: "#94a3b8", fontSize: 13 }}>
                    {newRegion
                      ? "لا توجد أحياء لهذه المنطقة"
                      : "اختر المنطقة أولا"}
                  </span>
                ) : (
                  addFilteredNeighborhoods.map((n) => (
                    <label
                      key={n.id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                        fontSize: 13,
                        padding: "4px 8px",
                        background: newNeighborhoodIds.includes(n.id)
                          ? "#dbeafe"
                          : "#f8fafc",
                        borderRadius: 6,
                        cursor: "pointer",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={newNeighborhoodIds.includes(n.id)}
                        onChange={() =>
                          toggleNeighborhood(
                            n.id,
                            newNeighborhoodIds,
                            setNewNeighborhoodIds
                          )
                        }
                      />
                      {n.name}
                    </label>
                  ))
                )}
              </div>
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? <span className="spinner" /> : "إضافة المختار"}
            </button>
          </form>
        ) : loading ? (
          <div style={{ textAlign: "center", padding: 40 }}>
            <div className="spinner spinner-dark" />
          </div>
        ) : getDisplayedMukhtars().length === 0 ? (
          <div className="empty-state">
            <div className="icon">🏛️</div>
            <p>لا يوجد مختارون</p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>الاسم</th>
                  <th>الهاتف</th>
                  <th>المنطقة</th>
                  <th>الأحياء</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {getDisplayedMukhtars().map((m, i) => (
                  <tr key={m.id}>
                    <td>{i + 1}</td>
                    <td>
                      {editId === m.id ? (
                        <input
                          className="form-input"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          style={{ padding: "4px 8px", fontSize: 13 }}
                        />
                      ) : (
                        <strong>{m.name}</strong>
                      )}
                    </td>
                    <td>
                      {editId === m.id ? (
                        <input
                          className="form-input"
                          value={editPhone}
                          onChange={(e) => setEditPhone(e.target.value)}
                          style={{ padding: "4px 8px", fontSize: 13 }}
                        />
                      ) : (
                        <span style={{ direction: "ltr", display: "inline-block" }}>
                          {m.phone || "-"}
                        </span>
                      )}
                    </td>
                    <td>
                      {editId === m.id ? (
                        <select
                          className="form-input"
                          value={editRegion}
                          onChange={(e) => {
                            setEditRegion(e.target.value);
                            setEditNeighborhoodIds([]);
                          }}
                          style={{ padding: "4px 8px", fontSize: 13 }}
                        >
                          <option value="">اختر</option>
                          {regions.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <span>{m.region || "-"}</span>
                      )}
                    </td>
                    <td>
                      {editId === m.id ? (
                        <div
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: 4,
                            maxHeight: 100,
                            overflowY: "auto",
                          }}
                        >
                          {editFilteredNeighborhoods.length === 0 ? (
                            <span style={{ color: "#94a3b8", fontSize: 11 }}>
                              {editRegion
                                ? "لا توجد أحياء"
                                : "اختر المنطقة"}
                            </span>
                          ) : (
                            editFilteredNeighborhoods.map((n) => (
                              <label
                                key={n.id}
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: 2,
                                  fontSize: 11,
                                  padding: "2px 6px",
                                  background: editNeighborhoodIds.includes(n.id)
                                    ? "#dbeafe"
                                    : "#f8fafc",
                                  borderRadius: 4,
                                  cursor: "pointer",
                                }}
                              >
                                <input
                                  type="checkbox"
                                  checked={editNeighborhoodIds.includes(n.id)}
                                  onChange={() =>
                                    toggleNeighborhood(
                                      n.id,
                                      editNeighborhoodIds,
                                      setEditNeighborhoodIds
                                    )
                                  }
                                />
                                {n.name}
                              </label>
                            ))
                          )}
                        </div>
                      ) : (
                        <span style={{ fontSize: 12 }}>
                          {m.neighborhoods?.join("، ") || "-"}
                        </span>
                      )}
                    </td>
                    <td>
                      {editId === m.id ? (
                        <div style={{ display: "flex", gap: 4 }}>
                          <button
                            onClick={handleUpdate}
                            className="btn btn-sm btn-success"
                          >
                            حفظ
                          </button>
                          <button
                            onClick={() => setEditId(null)}
                            className="btn btn-sm btn-outline"
                          >
                            إلغاء
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: "flex", gap: 4 }}>
                          <button
                            onClick={() => startEdit(m)}
                            className="btn btn-sm btn-primary"
                          >
                            تعديل
                          </button>
                          <button
                            onClick={() => handleDelete(m.id)}
                            className="btn btn-sm btn-danger"
                          >
                            حذف
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}

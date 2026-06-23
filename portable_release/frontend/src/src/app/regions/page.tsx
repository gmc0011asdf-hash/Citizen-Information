"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  getRegions,
  getRegionsWithIds,
  getNeighborhoods,
  addNeighborhood,
  deleteNeighborhood,
  addRegion,
  deleteRegion,
  updateRegion,
  updateNeighborhood,
} from "@/lib/api";
import type { Neighborhood } from "@/lib/types";

export default function RegionsPage() {
  const [regions, setRegions] = useState<string[]>([]);
  const [neighborhoods, setNeighborhoods] = useState<Neighborhood[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [newName, setNewName] = useState("");
  const [newRegion, setNewRegion] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);

  // Add region state
  const [newRegionName, setNewRegionName] = useState("");
  const [savingRegion, setSavingRegion] = useState(false);

  // Regions with IDs for editing
  const [regionsWithIds, setRegionsWithIds] = useState<Array<{ id: number; name: string }>>([]);

  // Edit state
  const [editingRegion, setEditingRegion] = useState<string | null>(null);
  const [editRegionName, setEditRegionName] = useState("");
  const [editingNeighborhood, setEditingNeighborhood] = useState<number | null>(null);
  const [editNeighborhoodName, setEditNeighborhoodName] = useState("");

  const fetchData = () => {
    setLoading(true);
    Promise.all([getRegions(), getNeighborhoods(), getRegionsWithIds()])
      .then(([r, n, rwi]) => {
        setRegions(r);
        setNeighborhoods(n);
        setRegionsWithIds(rwi);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredNeighborhoods = selectedRegion
    ? neighborhoods.filter((n) => n.region === selectedRegion)
    : neighborhoods;

  const handleAddNeighborhood = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!newName.trim() || !newRegion) {
      setError("يرجى إدخال اسم الحي واختيار المنطقة");
      return;
    }
    setSaving(true);
    try {
      await addNeighborhood(newName, newRegion);
      setSuccess("تم إضافة الحي بنجاح");
      setNewName("");
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في الإضافة");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteNeighborhood = async (id: number) => {
    if (!confirm("هل أنت متأكد من حذف هذا الحي؟")) return;
    try {
      await deleteNeighborhood(id);
      fetchData();
    } catch {
      /* ignore */
    }
  };

  const handleAddRegion = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!newRegionName.trim()) {
      setError("يرجى إدخال اسم المنطقة");
      return;
    }
    setSavingRegion(true);
    try {
      await addRegion(newRegionName);
      setSuccess("تم إضافة المنطقة بنجاح");
      setNewRegionName("");
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في إضافة المنطقة");
    } finally {
      setSavingRegion(false);
    }
  };

  const handleDeleteRegion = async (regionName: string) => {
    const regionNeighborhoods = neighborhoods.filter(
      (n) => n.region === regionName
    );
    if (regionNeighborhoods.length > 0) {
      setError(
        `لا يمكن حذف المنطقة "${regionName}" لأنها تحتوي على ${regionNeighborhoods.length} حي`
      );
      return;
    }
    if (!confirm(`هل أنت متأكد من حذف المنطقة "${regionName}"؟`)) return;
    try {
      const regionObj = regionsWithIds.find((r) => r.name === regionName);
      if (!regionObj) return;
      await deleteRegion(regionObj.id);
      if (selectedRegion === regionName) setSelectedRegion("");
      setSuccess("تم حذف المنطقة بنجاح");
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في حذف المنطقة");
    }
  };

  const handleEditRegion = async (regionName: string) => {
    if (!editRegionName.trim()) return;
    const regionObj = regionsWithIds.find((r) => r.name === regionName);
    if (!regionObj) return;
    try {
      await updateRegion(regionObj.id, editRegionName);
      setEditingRegion(null);
      setEditRegionName("");
      setSuccess("تم تعديل المنطقة بنجاح");
      if (selectedRegion === regionName) setSelectedRegion(editRegionName);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في تعديل المنطقة");
    }
  };

  const handleEditNeighborhood = async (n: Neighborhood) => {
    if (!editNeighborhoodName.trim()) return;
    try {
      await updateNeighborhood(n.id, editNeighborhoodName, n.region);
      setEditingNeighborhood(null);
      setEditNeighborhoodName("");
      setSuccess("تم تعديل الحي بنجاح");
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في تعديل الحي");
    }
  };

  return (
    <AppShell title="المناطق والأحياء">
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Regions list */}
        <div className="card">
          <h3 style={{ margin: "0 0 16px", color: "var(--navy)" }}>
            المناطق
          </h3>

          {/* Add region form */}
          <form
            onSubmit={handleAddRegion}
            style={{
              display: "flex",
              gap: 8,
              marginBottom: 16,
              alignItems: "end",
            }}
          >
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>إضافة منطقة جديدة</label>
              <input
                className="form-input"
                value={newRegionName}
                onChange={(e) => setNewRegionName(e.target.value)}
                placeholder="اسم المنطقة"
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={savingRegion}
              style={{ height: 42 }}
            >
              {savingRegion ? <span className="spinner" /> : "إضافة"}
            </button>
          </form>

          {loading ? (
            <div style={{ textAlign: "center", padding: 20 }}>
              <div className="spinner spinner-dark" />
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <button
                className={`btn ${!selectedRegion ? "btn-primary" : "btn-outline"}`}
                onClick={() => setSelectedRegion("")}
                style={{ justifyContent: "center" }}
              >
                الكل ({neighborhoods.length})
              </button>
              {regions.map((r) => {
                const count = neighborhoods.filter(
                  (n) => n.region === r
                ).length;
                return (
                  <div key={r}>
                    {editingRegion === r ? (
                      <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                        <input
                          className="form-input"
                          value={editRegionName}
                          onChange={(e) => setEditRegionName(e.target.value)}
                          onKeyDown={(e) => e.key === "Enter" && handleEditRegion(r)}
                          autoFocus
                          style={{ flex: 1 }}
                        />
                        <button
                          onClick={() => handleEditRegion(r)}
                          className="btn btn-sm btn-primary"
                          style={{ padding: "5px 8px", fontSize: 14 }}
                        >
                          حفظ
                        </button>
                        <button
                          onClick={() => { setEditingRegion(null); setEditRegionName(""); }}
                          className="btn btn-sm btn-outline"
                          style={{ padding: "5px 8px", fontSize: 14 }}
                        >
                          إلغاء
                        </button>
                      </div>
                    ) : (
                      <div
                        style={{
                          display: "flex",
                          gap: 4,
                          alignItems: "center",
                        }}
                      >
                        <button
                          className={`btn ${selectedRegion === r ? "btn-primary" : "btn-outline"}`}
                          onClick={() => setSelectedRegion(r)}
                          style={{ flex: 1, justifyContent: "space-between" }}
                        >
                          <span>{r}</span>
                          <span
                            style={{
                              background:
                                selectedRegion === r
                                  ? "rgba(255,255,255,0.2)"
                                  : "#f1f5f9",
                              padding: "2px 8px",
                              borderRadius: 12,
                              fontSize: 12,
                            }}
                          >
                            {count}
                          </span>
                        </button>
                        <button
                          onClick={() => { setEditingRegion(r); setEditRegionName(r); }}
                          className="btn btn-sm btn-outline"
                          title="تعديل المنطقة"
                          style={{ padding: "5px 8px", fontSize: 14 }}
                        >
                          تعديل
                        </button>
                        <button
                          onClick={() => handleDeleteRegion(r)}
                          className="btn btn-sm btn-danger"
                          title="حذف المنطقة"
                          style={{ padding: "5px 8px", fontSize: 14 }}
                        >
                          ✕
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Neighborhoods */}
        <div className="card">
          <h3 style={{ margin: "0 0 16px", color: "var(--navy)" }}>
            الأحياء {selectedRegion && `- ${selectedRegion}`}
          </h3>

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          {/* Add neighborhood form */}
          <form
            onSubmit={handleAddNeighborhood}
            style={{
              display: "flex",
              gap: 8,
              marginBottom: 16,
              alignItems: "end",
            }}
          >
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>اسم الحي</label>
              <input
                className="form-input"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="أدخل اسم الحي"
              />
            </div>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>المنطقة</label>
              <select
                className="form-input"
                value={newRegion}
                onChange={(e) => setNewRegion(e.target.value)}
              >
                <option value="">اختر المنطقة</option>
                {regions.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
              style={{ height: 42 }}
            >
              {saving ? <span className="spinner" /> : "إضافة"}
            </button>
          </form>

          {/* List */}
          {loading ? (
            <div style={{ textAlign: "center", padding: 20 }}>
              <div className="spinner spinner-dark" />
            </div>
          ) : filteredNeighborhoods.length === 0 ? (
            <div className="empty-state" style={{ padding: 20 }}>
              <p>لا توجد أحياء</p>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>اسم الحي</th>
                    <th>المنطقة</th>
                    <th>إجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredNeighborhoods.map((n, i) => (
                    <tr key={n.id}>
                      <td>{i + 1}</td>
                      <td>
                        {editingNeighborhood === n.id ? (
                          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                            <input
                              className="form-input"
                              value={editNeighborhoodName}
                              onChange={(e) => setEditNeighborhoodName(e.target.value)}
                              onKeyDown={(e) => e.key === "Enter" && handleEditNeighborhood(n)}
                              autoFocus
                              style={{ margin: 0 }}
                            />
                            <button
                              onClick={() => handleEditNeighborhood(n)}
                              className="btn btn-sm btn-primary"
                            >
                              حفظ
                            </button>
                            <button
                              onClick={() => { setEditingNeighborhood(null); setEditNeighborhoodName(""); }}
                              className="btn btn-sm btn-outline"
                            >
                              إلغاء
                            </button>
                          </div>
                        ) : (
                          n.name
                        )}
                      </td>
                      <td>{n.region}</td>
                      <td>
                        <div style={{ display: "flex", gap: 4 }}>
                          {editingNeighborhood !== n.id && (
                            <button
                              onClick={() => { setEditingNeighborhood(n.id); setEditNeighborhoodName(n.name); }}
                              className="btn btn-sm btn-outline"
                            >
                              تعديل
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteNeighborhood(n.id)}
                            className="btn btn-sm btn-danger"
                          >
                            حذف
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

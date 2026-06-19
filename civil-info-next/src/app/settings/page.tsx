"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  getUsers,
  addUser,
  deleteUser,
  changePassword,
  getRoles,
  getBackups,
  createBackup,
  deleteBackup,
} from "@/lib/api";
import type { User, Backup } from "@/lib/types";

type TabType = "users" | "backup" | "maintenance";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("users");
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        setCurrentUser(JSON.parse(stored));
      } catch {
        /* ignore */
      }
    }
  }, []);

  return (
    <AppShell title="الإعدادات">
      <div className="card">
        <div className="tabs">
          <button
            className={`tab ${activeTab === "users" ? "active" : ""}`}
            onClick={() => setActiveTab("users")}
          >
            المستخدمون
          </button>
          <button
            className={`tab ${activeTab === "backup" ? "active" : ""}`}
            onClick={() => setActiveTab("backup")}
          >
            النسخ الاحتياطي
          </button>
          <button
            className={`tab ${activeTab === "maintenance" ? "active" : ""}`}
            onClick={() => setActiveTab("maintenance")}
          >
            الصيانة
          </button>
        </div>

        {activeTab === "users" && <UsersTab currentUser={currentUser} />}
        {activeTab === "backup" && <BackupTab />}
        {activeTab === "maintenance" && (
          <MaintenanceTab currentUser={currentUser} />
        )}
      </div>
    </AppShell>
  );
}

function UsersTab({ currentUser }: { currentUser: User | null }) {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Add user form
  const [showAdd, setShowAdd] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newDisplayName, setNewDisplayName] = useState("");
  const [newRole, setNewRole] = useState("viewer");
  const [saving, setSaving] = useState(false);

  const fetchData = () => {
    setLoading(true);
    Promise.all([getUsers(), getRoles()])
      .then(([u, r]) => {
        setUsers(u);
        setRoles(r);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!newUsername.trim() || !newPassword.trim() || !newDisplayName.trim()) {
      setError("جميع الحقول مطلوبة");
      return;
    }
    setSaving(true);
    try {
      await addUser(newUsername, newPassword, newDisplayName, newRole);
      setSuccess("تم إضافة المستخدم بنجاح");
      setNewUsername("");
      setNewPassword("");
      setNewDisplayName("");
      setNewRole("viewer");
      setShowAdd(false);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في الإضافة");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("هل أنت متأكد من حذف هذا المستخدم؟")) return;
    setError("");
    try {
      await deleteUser(id);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ في الحذف");
    }
  };

  const roleLabel = (role: string) => {
    switch (role) {
      case "admin":
        return "مسؤول";
      case "editor":
        return "محرر";
      default:
        return "مشاهد";
    }
  };

  return (
    <div>
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <h3 style={{ margin: 0, color: "var(--navy)" }}>إدارة المستخدمين</h3>
        {currentUser?.role === "admin" && (
          <button
            className="btn btn-primary"
            onClick={() => setShowAdd(!showAdd)}
          >
            {showAdd ? "إلغاء" : "➕ إضافة مستخدم"}
          </button>
        )}
      </div>

      {showAdd && (
        <form
          onSubmit={handleAdd}
          style={{
            background: "#f8fafc",
            padding: 20,
            borderRadius: 12,
            marginBottom: 20,
          }}
        >
          <div className="form-grid">
            <div className="form-group">
              <label>اسم المستخدم</label>
              <input
                className="form-input"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>كلمة المرور</label>
              <input
                type="password"
                className="form-input"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>الاسم المعروض</label>
              <input
                className="form-input"
                value={newDisplayName}
                onChange={(e) => setNewDisplayName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>الدور</label>
              <select
                className="form-input"
                value={newRole}
                onChange={(e) => setNewRole(e.target.value)}
              >
                {roles.map((r) => (
                  <option key={r} value={r}>
                    {roleLabel(r)}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={saving}
          >
            {saving ? <span className="spinner" /> : "إضافة"}
          </button>
        </form>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: 40 }}>
          <div className="spinner spinner-dark" />
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>اسم المستخدم</th>
              <th>الاسم المعروض</th>
              <th>الدور</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u, i) => (
              <tr key={u.id}>
                <td>{i + 1}</td>
                <td>{u.username}</td>
                <td>{u.display_name}</td>
                <td>
                  <span className="badge badge-active">
                    {roleLabel(u.role)}
                  </span>
                </td>
                <td>
                  {currentUser?.role === "admin" &&
                    u.id !== currentUser?.id && (
                      <button
                        onClick={() => handleDelete(u.id)}
                        className="btn btn-sm btn-danger"
                      >
                        حذف
                      </button>
                    )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function BackupTab() {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchData = () => {
    setLoading(true);
    getBackups()
      .then(setBackups)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async () => {
    setCreating(true);
    setError("");
    setSuccess("");
    try {
      const res = await createBackup();
      setSuccess(`تم إنشاء النسخة الاحتياطية: ${res.name}`);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm("هل أنت متأكد من حذف هذه النسخة الاحتياطية؟")) return;
    try {
      await deleteBackup(name);
      fetchData();
    } catch {
      /* ignore */
    }
  };

  return (
    <div>
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <h3 style={{ margin: 0, color: "var(--navy)" }}>النسخ الاحتياطي</h3>
        <button
          className="btn btn-primary"
          onClick={handleCreate}
          disabled={creating}
        >
          {creating ? <span className="spinner" /> : "إنشاء نسخة احتياطية"}
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 40 }}>
          <div className="spinner spinner-dark" />
        </div>
      ) : backups.length === 0 ? (
        <div className="empty-state">
          <div className="icon">💾</div>
          <p>لا توجد نسخ احتياطية</p>
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>اسم الملف</th>
              <th>الحجم (MB)</th>
              <th>التاريخ</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            {backups.map((b, i) => (
              <tr key={b.name}>
                <td>{i + 1}</td>
                <td style={{ fontSize: 13 }}>{b.name}</td>
                <td>{b.size_mb}</td>
                <td>{b.date}</td>
                <td>
                  <button
                    onClick={() => handleDelete(b.name)}
                    className="btn btn-sm btn-danger"
                  >
                    حذف
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function MaintenanceTab({ currentUser }: { currentUser: User | null }) {
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!oldPw || !newPw || !confirmPw) {
      setError("جميع الحقول مطلوبة");
      return;
    }
    if (newPw !== confirmPw) {
      setError("كلمة المرور الجديدة غير متطابقة");
      return;
    }
    if (!currentUser) return;
    setSaving(true);
    try {
      await changePassword(currentUser.id, oldPw, newPw);
      setSuccess("تم تغيير كلمة المرور بنجاح");
      setOldPw("");
      setNewPw("");
      setConfirmPw("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطأ");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h3 style={{ margin: "0 0 20px", color: "var(--navy)" }}>
        تغيير كلمة المرور
      </h3>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form
        onSubmit={handleChangePassword}
        style={{ maxWidth: 400 }}
      >
        <div className="form-group">
          <label>كلمة المرور الحالية</label>
          <input
            type="password"
            className="form-input"
            value={oldPw}
            onChange={(e) => setOldPw(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>كلمة المرور الجديدة</label>
          <input
            type="password"
            className="form-input"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>تأكيد كلمة المرور الجديدة</label>
          <input
            type="password"
            className="form-input"
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            required
          />
        </div>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={saving}
        >
          {saving ? <span className="spinner" /> : "تغيير كلمة المرور"}
        </button>
      </form>
    </div>
  );
}

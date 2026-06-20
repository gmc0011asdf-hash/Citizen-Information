"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import type { User } from "@/lib/types";

const allNavItems = [
  { href: "/people", label: "قائمة الأشخاص", icon: "👥", roles: ["viewer", "editor", "admin"] },
  { href: "/people/new", label: "إضافة شخص", icon: "➕", roles: ["editor", "admin"] },
  { href: "/statistics", label: "إحصائيات", icon: "📊", roles: ["viewer", "editor", "admin"] },
  { href: "/mukhtars", label: "المختارون", icon: "🏛️", roles: ["editor", "admin"] },
  { href: "/regions", label: "المناطق والأحياء", icon: "🗺️", roles: ["editor", "admin"] },
  { href: "/deleted", label: "المحذوفات", icon: "🗑️", roles: ["admin"] },
  { href: "/settings", label: "الإعدادات", icon: "⚙️", roles: ["admin"] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [perPage, setPerPage] = useState(50);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        /* ignore */
      }
    }
    const storedPerPage = localStorage.getItem("perPage");
    if (storedPerPage) setPerPage(Number(storedPerPage));
  }, []);

  const handlePerPageChange = (val: string) => {
    const n = Number(val);
    setPerPage(n);
    localStorage.setItem("perPage", String(n));
    window.dispatchEvent(new CustomEvent("perPageChanged", { detail: n }));
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    window.location.href = "/";
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
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">🏛️</div>
        <h1>المعلومات المدنية للمواطنين</h1>
      </div>

      {user && (
        <div className="sidebar-user">
          <div className="avatar">
            {user.display_name?.charAt(0) || user.username?.charAt(0) || "م"}
          </div>
          <div className="user-info">
            <div className="user-name">
              {user.display_name || user.username}
            </div>
            <div className="user-role">{roleLabel(user.role)}</div>
          </div>
        </div>
      )}

      <nav className="sidebar-nav">
        {allNavItems
          .filter((item) => !user || item.roles.includes(user.role))
          .map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href) && item.href !== "/people/new") ||
              (item.href === "/people/new" && pathname === "/people/new");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={isActive ? "active" : ""}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
      </nav>

      <div className="sidebar-per-page">
        <label>عدد السجلات في الصفحة</label>
        <select
          value={perPage}
          onChange={(e) => handlePerPageChange(e.target.value)}
        >
          <option value="25">25</option>
          <option value="50">50</option>
          <option value="100">100</option>
          <option value="200">200</option>
        </select>
      </div>

      {user && (
        <div style={{ padding: "8px 20px" }}>
          <button
            onClick={handleLogout}
            className="btn btn-outline"
            style={{
              width: "100%",
              color: "rgba(255,255,255,0.7)",
              borderColor: "rgba(255,255,255,0.2)",
              fontSize: "13px",
            }}
          >
            تسجيل خروج
          </button>
        </div>
      )}

      <div className="sidebar-footer">
        تم إنشاء النظام بواسطة
        <br />
        <span className="creator-name">احمد الذهبي</span>
        <br />
        07711228946
        <br />
        07822667735
      </div>
    </aside>
  );
}

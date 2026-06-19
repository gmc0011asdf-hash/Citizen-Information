"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { getStats, getDistribution } from "@/lib/api";
import type { Stats, Distribution } from "@/lib/types";

export default function StatisticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [regionDist, setRegionDist] = useState<Distribution[]>([]);
  const [hayDist, setHayDist] = useState<Distribution[]>([]);
  const [jobDist, setJobDist] = useState<Distribution[]>([]);
  const [maritalDist, setMaritalDist] = useState<Distribution[]>([]);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getStats(),
      getDistribution("المنطقة", 15),
      getDistribution("الحي", 15),
      getDistribution("المهنة", 15),
      getDistribution("الحالة_الزوجية", 10),
    ])
      .then(([s, rd, hd, jd, md]) => {
        setStats(s);
        setRegionDist(rd);
        setHayDist(hd);
        setJobDist(jd);
        setMaritalDist(md);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <AppShell title="إحصائيات">
        <div style={{ textAlign: "center", padding: 60 }}>
          <div className="spinner spinner-dark" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="إحصائيات">
      {/* Row 1: Main stats */}
      <div className="stat-cards" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <div className="stat-card">
          <div className="stat-value">{stats?.total ?? 0}</div>
          <div className="stat-label">إجمالي السجلات</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.active ?? 0}</div>
          <div className="stat-label">النشطة</div>
        </div>
        <div className="stat-card danger">
          <div className="stat-value">{stats?.deleted ?? 0}</div>
          <div className="stat-label">المحذوفات</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.with_full_name ?? 0}</div>
          <div className="stat-label">بأسماء كاملة</div>
        </div>
      </div>

      {/* Row 2: Gold stats */}
      <div className="stat-cards" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
        <div className="stat-card gold">
          <div className="stat-value">{stats?.mukhtars ?? 0}</div>
          <div className="stat-label">المختارون</div>
        </div>
        <div className="stat-card gold">
          <div className="stat-value">{stats?.neighborhoods ?? 0}</div>
          <div className="stat-label">الأحياء</div>
        </div>
        <div className="stat-card gold">
          <div className="stat-value">{stats?.unique_jobs ?? 0}</div>
          <div className="stat-label">المهن الفريدة</div>
        </div>
      </div>

      {/* Distribution Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <ChartCard title="توزيع المناطق" data={regionDist} />
        <ChartCard title="توزيع الأحياء" data={hayDist} />
        <ChartCard title="توزيع المهن" data={jobDist} />
        <ChartCard title="الحالة الزوجية" data={maritalDist} />
      </div>
    </AppShell>
  );
}

function ChartCard({
  title,
  data,
}: {
  title: string;
  data: Distribution[];
}) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="card">
      <h3 style={{ margin: "0 0 16px", color: "var(--navy)", fontSize: 16 }}>
        {title}
      </h3>
      {data.length === 0 ? (
        <div className="empty-state" style={{ padding: 20 }}>
          <p>لا توجد بيانات</p>
        </div>
      ) : (
        data.map((item, i) => (
          <div key={i} className="chart-bar-container">
            <div className="chart-bar-label">
              <span>{item.value || "غير محدد"}</span>
              <span style={{ fontWeight: 600 }}>{item.count}</span>
            </div>
            <div className="chart-bar-track">
              <div
                className="chart-bar-fill"
                style={{ width: `${(item.count / maxCount) * 100}%` }}
              />
            </div>
          </div>
        ))
      )}
    </div>
  );
}

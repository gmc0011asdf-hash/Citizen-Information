"use client";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

interface AppShellProps {
  title: string;
  children: React.ReactNode;
}

export default function AppShell({ title, children }: AppShellProps) {
  return (
    <>
      <Sidebar />
      <Topbar title={title} />
      <main className="main-content">{children}</main>
    </>
  );
}

"use client";

import { useEffect, useState } from "react";

interface TopbarProps {
  title: string;
}

export default function Topbar({ title }: TopbarProps) {
  const [time, setTime] = useState("");
  const [date, setDate] = useState("");

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      // Baghdad time UTC+3
      const baghdad = new Date(
        now.toLocaleString("en-US", { timeZone: "Asia/Baghdad" })
      );
      const hours = baghdad.getHours().toString().padStart(2, "0");
      const minutes = baghdad.getMinutes().toString().padStart(2, "0");
      const seconds = baghdad.getSeconds().toString().padStart(2, "0");
      setTime(`${hours}:${minutes}:${seconds}`);

      const arabicDate = baghdad.toLocaleDateString("ar-IQ", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      });
      setDate(arabicDate);
    };

    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="topbar">
      <h2 className="topbar-title">{title}</h2>
      <div className="topbar-clock">
        <span>{date}</span>
        <span className="time">{time}</span>
      </div>
    </header>
  );
}

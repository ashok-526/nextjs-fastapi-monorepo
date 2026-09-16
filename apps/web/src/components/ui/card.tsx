import * as React from "react"

export function Card({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <div className={["rounded-lg border border-slate-200 bg-white", className].join(" ")}>{children}</div>
}

export function CardHeader({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <div className={["border-b border-slate-200 p-4", className].join(" ")}>{children}</div>
}

export function CardContent({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <div className={["p-4", className].join(" ")}>{children}</div>
}


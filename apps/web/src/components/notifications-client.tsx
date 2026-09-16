"use client"
import * as React from "react"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE as string

async function getToken(): Promise<string | null> {
  const res = await fetch("/api/ws-token", { cache: "no-store" })
  if (!res.ok) return null
  const data = await res.json()
  return data.token ?? null
}

export function NotificationsClient() {
  const [count, setCount] = React.useState(0)
  const [events, setEvents] = React.useState<any[]>([])

  React.useEffect(() => {
    let ws: WebSocket | null = null
    let active = true
    getToken().then((token) => {
      if (!token || !active) return
      const wsUrl = API_BASE.replace("http", "ws") + `/ws?token=${encodeURIComponent(token)}`
      ws = new WebSocket(wsUrl)
      ws.onmessage = (ev) => {
        try {
          const evt = JSON.parse(ev.data)
          setEvents((list) => [evt, ...list].slice(0, 50))
          setCount((c) => c + 1)
        } catch {}
      }
    })
    return () => { active = false; if (ws) ws.close() }
  }, [])

  return (
    <div className="space-y-3">
      <div className="text-sm">Unread: <span className="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-slate-900 px-2 text-white">{count}</span></div>
      <ul className="space-y-2">
        {events.map((e, i) => (
          <li key={i} className="rounded border border-slate-200 p-2 text-sm">{JSON.stringify(e)}</li>
        ))}
      </ul>
    </div>
  )
}


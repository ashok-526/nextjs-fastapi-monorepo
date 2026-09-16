const PROXY = "/api/proxy"

async function fetchReports() {
  const res = await fetch(`${PROXY}?path=admin/reports`, { cache: "no-store" })
  if (!res.ok) return { data: [] }
  return res.json()
}

export default async function AdminReportsPage() {
  const data = await fetchReports()
  return (
    <main className="mx-auto max-w-2xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Admin Reports</h1>
      <ul className="space-y-2">
        {data.data.map((r: any) => (
          <li key={r.id} className="rounded border border-slate-200 p-3 text-sm">
            <div><strong>Post:</strong> {r.post_id}</div>
            <div><strong>Reporter:</strong> {r.reporter_id}</div>
            <div><strong>Reason:</strong> {r.reason}</div>
            <div className="text-slate-500"><strong>At:</strong> {r.created_at}</div>
          </li>
        ))}
        {data.data.length === 0 && <div className="text-sm text-slate-500">No reports.</div>}
      </ul>
    </main>
  )
}


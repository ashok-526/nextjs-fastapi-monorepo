import { cookies } from "next/headers"
import { QueryProvider } from "@/components/query-provider"
import { FeedClient } from "@/components/feed-client"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE as string

async function fetchInitialFeed() {
  const token = cookies().get("token")?.value
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) headers["Authorization"] = `Bearer ${token}`
  const res = await fetch(`${API_BASE}/feed`, { headers, cache: "no-store" })
  if (!res.ok) return { data: [], next_cursor: null }
  return res.json()
}

export default async function Page() {
  const initial = await fetchInitialFeed()
  return (
    <main className="mx-auto max-w-xl p-6">
      <h1 className="mb-4 text-2xl font-semibold">Home</h1>
      <QueryProvider>
        <FeedClient initial={initial.data} nextCursor={initial.next_cursor} />
      </QueryProvider>
    </main>
  )
}

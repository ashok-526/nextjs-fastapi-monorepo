"use client"
import * as React from "react"
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

type Visibility = "public" | "friends" | "private"
type Post = {
  id: string
  author_id: string
  body: string
  media_json?: { images?: string[] }
  visibility: Visibility
  created_at?: string
}

const PROXY = "/api/proxy"

async function fetchFeed(cursor?: string) {
  const url = new URL(PROXY, location.origin)
  url.searchParams.set("path", "feed")
  if (cursor) url.searchParams.set("cursor", cursor)
  const res = await fetch(url.toString(), { cache: "no-store" })
  if (!res.ok) throw new Error("failed")
  return res.json() as Promise<{ data: Post[]; next_cursor?: string | null }>
}

export function FeedClient({ initial, nextCursor }: { initial: Post[]; nextCursor?: string | null }) {
  const qc = useQueryClient()
  const [optimistic, setOptimistic] = React.useState<Record<string, boolean>>({})

  const query = useInfiniteQuery({
    queryKey: ["feed"],
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) => fetchFeed(pageParam),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    initialData: {
      pages: [{ data: initial, next_cursor: nextCursor ?? undefined }],
      pageParams: [undefined],
    } as any,
  })

  const toggleReaction = async (postId: string) => {
    const liked = !!optimistic[postId]
    setOptimistic((s) => ({ ...s, [postId]: !liked }))
    try {
      if (!liked) {
        await fetch(`${PROXY}?path=posts/${postId}/react`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ type: "like" }),
        })
      } else {
        await fetch(`${PROXY}?path=posts/${postId}/react`, { method: "DELETE" })
      }
    } catch (e) {
      setOptimistic((s) => ({ ...s, [postId]: liked }))
    }
  }

  const items = query.data?.pages.flatMap((p) => p.data) ?? initial

  return (
    <div className="space-y-4">
      {items.map((p) => (
        <Card key={p.id}>
          <CardContent>
            <div className="text-sm text-slate-500">{new Date(p.created_at ?? '').toLocaleString()}</div>
            <p className="mt-2 whitespace-pre-wrap">{p.body}</p>
            {p.media_json?.images && p.media_json.images.length > 0 && (
              <div className="mt-2 grid grid-cols-2 gap-2">
                {p.media_json.images.slice(0,4).map((src) => (
                  <img key={src} src={src} className="h-40 w-full rounded object-cover" />
                ))}
              </div>
            )}
            <div className="mt-3">
              <Button size="sm" variant={optimistic[p.id] ? "default" : "outline"} onClick={() => toggleReaction(p.id)}>
                {optimistic[p.id] ? "Liked" : "Like"}
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
      <div className="py-4 text-center">
        {query.hasNextPage ? (
          <Button onClick={() => query.fetchNextPage()} disabled={query.isFetchingNextPage}>
            {query.isFetchingNextPage ? "Loading..." : "Load more"}
          </Button>
        ) : (
          <span className="text-sm text-slate-500">No more posts</span>
        )}
      </div>
    </div>
  )
}


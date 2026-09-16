"use client"

import * as React from "react"
import { Uploader } from "@/components/uploader"

const PROXY = "/api/proxy"

type Visibility = "public" | "friends" | "private"

export default function ComposePage() {
  const [body, setBody] = React.useState("")
  const [visibility, setVisibility] = React.useState<Visibility>("public")
  const [images, setImages] = React.useState<string[]>([])
  const [busy, setBusy] = React.useState(false)
  const [result, setResult] = React.useState<string | null>(null)

  const submit = async () => {
    if (!body.trim()) return
    setBusy(true)
    setResult(null)
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") ?? undefined : undefined
      const res = await fetch(`${PROXY}?path=posts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ body, media_json: images.length ? { images } : undefined, visibility }),
      })
      if (!res.ok) throw new Error("Failed to create post")
      const data = await res.json()
      setResult(`Posted: ${data.id}`)
      setBody("")
      setImages([])
    } catch (e: any) {
      setResult(e?.message ?? "Error")
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="mx-auto max-w-xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Compose</h1>
      <textarea
        className="w-full min-h-[120px] rounded border border-slate-300 p-2"
        placeholder="What's happening?"
        value={body}
        onChange={(e) => setBody(e.target.value)}
      />
      <div className="flex items-center gap-2">
        <label className="text-sm">Visibility</label>
        <select
          className="rounded border border-slate-300 p-1 text-sm"
          value={visibility}
          onChange={(e) => setVisibility(e.target.value as Visibility)}
        >
          <option value="public">Public</option>
          <option value="friends">Friends</option>
          <option value="private">Private</option>
        </select>
      </div>
      <Uploader onUploaded={setImages} max={4} />
      <button
        className="inline-flex items-center rounded bg-slate-900 px-4 py-2 text-white disabled:opacity-50"
        onClick={submit}
        disabled={busy}
      >
        {busy ? "Posting..." : "Post"}
      </button>
      {result && <p className="text-sm text-slate-600">{result}</p>}
    </main>
  )
}

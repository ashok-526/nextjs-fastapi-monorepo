"use client"

import * as React from "react"

type PresignResponse = {
  url: string
  fields: Record<string, string>
}

type UploaderProps = {
  onUploaded?: (urls: string[]) => void
  max?: number
}

const CDN_BASE = process.env.NEXT_PUBLIC_CDN_URL as string
const PROXY = "/api/proxy"

async function presign(file: File, token?: string): Promise<PresignResponse> {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? ""
  const res = await fetch(`${PROXY}?path=media/presign`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ contentType: file.type, ext, size: file.size }),
  })
  if (!res.ok) throw new Error("Failed to presign")
  return res.json()
}

async function uploadToS3(url: string, fields: Record<string, string>, file: File) {
  const form = new FormData()
  Object.entries(fields).forEach(([k, v]) => form.append(k, v))
  form.append("file", file)
  const res = await fetch(url, { method: "POST", body: form })
  if (!res.ok) throw new Error("Upload failed")
  return fields.key
}

export function Uploader({ onUploaded, max = 4 }: UploaderProps) {
  const [busy, setBusy] = React.useState(false)
  const [urls, setUrls] = React.useState<string[]>([])
  const inputRef = React.useRef<HTMLInputElement>(null)

  React.useEffect(() => {
    onUploaded?.(urls)
  }, [urls, onUploaded])

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    setBusy(true)
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") ?? undefined : undefined
      const slice = Array.from(files).slice(0, Math.max(1, Math.min(max, 4)))
      const uploaded: string[] = []
      for (const f of slice) {
        const { url, fields } = await presign(f, token)
        const key = await uploadToS3(url, fields, f)
        uploaded.push(`${CDN_BASE}/${key}`)
      }
      setUrls((prev) => [...prev, ...uploaded].slice(0, max))
    } catch (e) {
      console.error(e)
    } finally {
      setBusy(false)
      if (inputRef.current) inputRef.current.value = ""
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={(e) => handleFiles(e.target.files)}
          disabled={busy}
        />
        <span className="text-sm text-slate-500">Up to {max} images</span>
      </div>
      {urls.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {urls.map((u) => (
            <img key={u} src={u} alt="uploaded" className="h-32 w-full object-cover rounded" />
          ))}
        </div>
      )}
    </div>
  )
}

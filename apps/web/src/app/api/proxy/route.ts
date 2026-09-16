import { cookies } from "next/headers"
import { NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE as string

function buildUrl(path: string, searchParams: URLSearchParams) {
  const u = new URL(path, API_BASE + (API_BASE.endsWith("/") ? "" : "/"))
  searchParams.forEach((v, k) => {
    if (k !== "path") u.searchParams.append(k, v)
  })
  return u.toString()
}

async function forward(req: Request, method: string) {
  const { searchParams } = new URL(req.url)
  const path = searchParams.get("path") || ""
  const url = buildUrl(path, searchParams)
  const token = cookies().get("token")?.value
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const init: RequestInit = { method, headers, cache: "no-store" }
  if (method !== "GET") {
    const body = await req.text()
    if (body) init.body = body
  }
  const res = await fetch(url, init)
  const data = await res.text()
  return new NextResponse(data, { status: res.status, headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" } })
}

export async function GET(req: Request) {
  return forward(req, "GET")
}

export async function POST(req: Request) {
  return forward(req, "POST")
}

export async function DELETE(req: Request) {
  return forward(req, "DELETE")
}


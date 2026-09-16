import { cookies } from "next/headers"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import * as React from "react"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE as string

async function fetchProfile(username: string) {
  const token = cookies().get("token")?.value
  const headers: Record<string, string> = { }
  if (token) headers["Authorization"] = `Bearer ${token}`
  const res = await fetch(`${API_BASE}/users/${username}`, { headers, cache: "no-store" })
  if (!res.ok) return null
  return res.json()
}

export default async function UserPage({ params }: { params: { username: string } }) {
  const data = await fetchProfile(params.username)
  if (!data) return <main className="p-6">Not found</main>

  return (
    <main className="mx-auto max-w-xl p-6 space-y-4">
      <Card>
        <CardHeader>
          <h1 className="text-xl font-semibold">@{data.username}</h1>
        </CardHeader>
        <CardContent>
          <Tabs profile={data.profile} />
        </CardContent>
      </Card>
    </main>
  )
}

function Tabs({ profile }: { profile: any }) {
  'use client'
  const [tab, setTab] = React.useState<'posts'|'about'|'friends'>('posts')
  return (
    <div>
      <div className="flex gap-2">
        <Button variant={tab==='posts'? 'default':'outline'} onClick={()=>setTab('posts')}>Posts</Button>
        <Button variant={tab==='about'? 'default':'outline'} onClick={()=>setTab('about')}>About</Button>
        <Button variant={tab==='friends'? 'default':'outline'} onClick={()=>setTab('friends')}>Friends</Button>
      </div>
      <div className="mt-4">
        {tab==='posts' && <div className="text-sm text-slate-600">User posts coming soon.</div>}
        {tab==='about' && (
          <div className="space-y-1 text-sm">
            <div><strong>Name:</strong> {profile.full_name ?? '—'}</div>
            <div><strong>Bio:</strong> {profile.bio ?? '—'}</div>
            <div><strong>Location:</strong> {profile.location ?? '—'}</div>
            <div><strong>Website:</strong> {profile.website ?? '—'}</div>
            <div><strong>Visibility:</strong> {profile.visibility}</div>
          </div>
        )}
        {tab==='friends' && <div className="text-sm text-slate-600">Friends list coming soon.</div>}
      </div>
    </div>
  )
}


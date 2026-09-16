import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE as string

async function loginAction(formData: FormData) {
  'use server'
  const email_or_username = String(formData.get('email_or_username') || '')
  const password = String(formData.get('password') || '')
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email_or_username, password }),
  })
  if (!res.ok) {
    redirect('/login?error=1')
  }
  const data = await res.json()
  cookies().set('token', data.access_token, { httpOnly: true, sameSite: 'lax', path: '/' })
  redirect('/')
}

export default function LoginPage() {
  return (
    <main className="mx-auto max-w-sm p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Login</h1>
      <form action={loginAction} className="space-y-3">
        <Input name="email_or_username" placeholder="Email or username" required />
        <Input name="password" type="password" placeholder="Password" required />
        <Button type="submit" className="w-full">Login</Button>
      </form>
    </main>
  )
}


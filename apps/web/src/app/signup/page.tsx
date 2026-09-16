import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE as string

async function signupAction(formData: FormData) {
  'use server'
  const email = String(formData.get('email') || '')
  const username = String(formData.get('username') || '')
  const password = String(formData.get('password') || '')
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password }),
  })
  if (!res.ok) {
    redirect('/signup?error=1')
  }
  const data = await res.json()
  cookies().set('token', data.access_token, { httpOnly: true, sameSite: 'lax', path: '/' })
  redirect('/')
}

export default function SignupPage() {
  return (
    <main className="mx-auto max-w-sm p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Sign up</h1>
      <form action={signupAction} className="space-y-3">
        <Input name="email" placeholder="Email" type="email" required />
        <Input name="username" placeholder="Username" required />
        <Input name="password" type="password" placeholder="Password" required />
        <Button type="submit" className="w-full">Create account</Button>
      </form>
    </main>
  )
}


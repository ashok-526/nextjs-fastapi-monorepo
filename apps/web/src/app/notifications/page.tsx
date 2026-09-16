import { NotificationsClient } from "@/components/notifications-client"

export default function NotificationsPage() {
  return (
    <main className="mx-auto max-w-xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Notifications</h1>
      <NotificationsClient />
    </main>
  )
}


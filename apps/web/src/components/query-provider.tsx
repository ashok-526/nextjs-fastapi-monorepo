"use client"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import * as React from "react"

const client = new QueryClient()

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}


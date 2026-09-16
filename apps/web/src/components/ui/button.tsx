"use client"
import * as React from "react"

type Variant = "default" | "outline"
type Size = "sm" | "md" | "lg"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
}

const base = "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none disabled:opacity-50 disabled:pointer-events-none"
const variants: Record<Variant, string> = {
  default: "bg-slate-900 text-white hover:bg-slate-900/90",
  outline: "border border-slate-200 bg-white hover:bg-slate-100",
}
const sizes: Record<Size, string> = {
  sm: "h-9 px-3",
  md: "h-10 px-4",
  lg: "h-11 px-5",
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "default", size = "md", ...props }, ref) => (
    <button ref={ref} className={[base, variants[variant], sizes[size], className].join(" ")} {...props} />
  )
)
Button.displayName = "Button"


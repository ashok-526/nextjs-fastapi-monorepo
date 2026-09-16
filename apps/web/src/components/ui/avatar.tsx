"use client"
import * as React from "react"

export interface AvatarProps extends React.ImgHTMLAttributes<HTMLImageElement> {}

export function Avatar({ className = "", ...props }: AvatarProps) {
  return <img className={["h-10 w-10 rounded-full object-cover", className].join(" ")} {...props} />
}


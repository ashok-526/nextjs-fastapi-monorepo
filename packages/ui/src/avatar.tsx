"use client"
import * as React from 'react'
import { cn } from './utils'

export interface AvatarProps extends React.ImgHTMLAttributes<HTMLImageElement> {}

export function Avatar({ className, ...props }: AvatarProps) {
  return <img className={cn('h-10 w-10 rounded-full object-cover', className)} {...props} />
}


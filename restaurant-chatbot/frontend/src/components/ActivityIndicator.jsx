import React from 'react'
import { Loader2 } from 'lucide-react'

export const ActivityIndicator = ({ message }) => {
  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-chat-secondary rounded-lg animate-fadeIn">
      <Loader2 size={16} className="text-accent animate-spin" />
      <span className="text-sm text-gray-400">{message}</span>
    </div>
  )
}

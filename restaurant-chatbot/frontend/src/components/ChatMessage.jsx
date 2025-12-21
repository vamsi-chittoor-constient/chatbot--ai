import React from 'react'
import { User, Bot } from 'lucide-react'

export const ChatMessage = ({ message }) => {
  const isUser = message.role === 'user'

  return (
    <div className={`p-5 rounded-lg animate-fadeIn ${isUser ? 'bg-chat-user' : 'bg-chat-assistant'}`}>
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-7 h-7 rounded flex items-center justify-center ${isUser ? 'bg-purple-600' : 'bg-accent'}`}>
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>
        <span className="font-semibold text-sm">{isUser ? 'You' : 'Assistant'}</span>
      </div>
      <div className="text-[15px] leading-relaxed whitespace-pre-wrap">
        {message.content}
        {message.isStreaming && (
          <span className="inline-block w-2 h-4 bg-accent ml-1 animate-pulse-slow" />
        )}
      </div>
    </div>
  )
}

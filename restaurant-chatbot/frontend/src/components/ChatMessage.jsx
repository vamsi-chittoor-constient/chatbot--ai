import React from 'react'
import { User, Bot } from 'lucide-react'

/**
 * Parse basic markdown inline elements into React nodes.
 * Supports: **bold**, [text](url), and plain URLs (https://...)
 */
function renderMarkdown(text) {
  if (!text) return null

  // Split by markdown patterns: **bold**, [link](url), and bare URLs
  const parts = []
  // Regex: match **bold**, [text](url), or https://... URLs
  const regex = /(\*\*(.+?)\*\*)|(\[([^\]]+)\]\(([^)]+)\))|(https?:\/\/[^\s<]+)/g
  let lastIndex = 0
  let match

  while ((match = regex.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }

    if (match[1]) {
      // **bold**
      parts.push(<strong key={match.index} className="font-semibold">{match[2]}</strong>)
    } else if (match[3]) {
      // [text](url)
      parts.push(
        <a
          key={match.index}
          href={match[5]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent hover:underline"
        >
          {match[4]}
        </a>
      )
    } else if (match[6]) {
      // Bare URL
      parts.push(
        <a
          key={match.index}
          href={match[6]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent hover:underline break-all"
        >
          {match[6]}
        </a>
      )
    }

    lastIndex = match.index + match[0].length
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 0 ? parts : text
}

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
        {renderMarkdown(message.content)}
        {message.isStreaming && (
          <span className="inline-block w-2 h-4 bg-accent ml-1 animate-pulse-slow" />
        )}
      </div>
    </div>
  )
}

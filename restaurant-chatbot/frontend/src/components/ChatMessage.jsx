import React from 'react'
import { User } from 'lucide-react'
import Lottie from 'lottie-react'
import aibot from '../animations/aibot.json'

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
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fadeIn`}>
      <div className="flex items-start max-w-[85%]">
        {/* Bot Lottie Animation Avatar */}
        {!isUser && (
          <Lottie
            animationData={aibot}
            loop={true}
            className="w-14 h-14 flex-shrink-0"
          />
        )}

        {/* Message Bubble with their styling */}
        <div className={`
          ${isUser
            ? 'bg-red-600 text-white rounded-xl p-3 ml-0'
            : 'bg-white text-gray-900 border border-gray-200 rounded-xl p-3 ml-2'
          }
        `}>
          <div className="text-[15px] leading-relaxed whitespace-pre-wrap break-words">
            {renderMarkdown(message.content)}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 bg-red-500 ml-1 animate-pulse-slow" />
            )}
          </div>
        </div>

        {/* User Icon */}
        {isUser && (
          <div className="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center ml-2 flex-shrink-0">
            <User size={20} className="text-white" />
          </div>
        )}
      </div>
    </div>
  )
}

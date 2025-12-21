import React, { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'

export const ChatInput = ({ onSend, disabled }) => {
  const [message, setMessage] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [message])

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="bg-chat-secondary border-t border-chat-border p-4">
      <div className="max-w-3xl mx-auto">
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <div className="flex-1 flex items-end bg-chat-bg border border-chat-border rounded-xl p-1 focus-within:border-accent transition-colors">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              disabled={disabled}
              rows={1}
              className="flex-1 bg-transparent text-white text-[15px] px-3 py-2.5 resize-none focus:outline-none placeholder-gray-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!message.trim() || disabled}
              className="p-2.5 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
        <p className="text-center text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}

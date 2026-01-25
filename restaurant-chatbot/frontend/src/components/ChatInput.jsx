import React, { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff, Globe } from 'lucide-react'

// Supported languages for voice mode
const VOICE_LANGUAGES = [
  { code: 'English', label: 'English' },
  { code: 'Hindi', label: 'हिंदी' },
  { code: 'Tamil', label: 'தமிழ்' },
]

export const ChatInput = ({
  onSend,
  disabled,
  // Voice props
  onToggleVoiceMode = () => {},
  voiceModeActive = false,
  selectedLanguage = 'English',
  onLanguageChange = () => {}
}) => {
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

  const handleVoiceToggle = () => {
    onToggleVoiceMode()
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
              placeholder={voiceModeActive ? "Voice mode active..." : "Type your message..."}
              disabled={disabled || voiceModeActive}
              rows={1}
              className="flex-1 bg-transparent text-white text-[15px] px-3 py-2.5 resize-none focus:outline-none placeholder-gray-500 disabled:opacity-50"
            />

            {/* Language Selector */}
            <div className="relative">
              <select
                value={selectedLanguage}
                onChange={(e) => onLanguageChange(e.target.value)}
                disabled={disabled || voiceModeActive}
                className="appearance-none bg-chat-bg text-white text-sm px-2 py-2.5 pr-6 rounded-lg border border-chat-border focus:outline-none focus:border-accent disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                title="Select voice language"
              >
                {VOICE_LANGUAGES.map(lang => (
                  <option key={lang.code} value={lang.code}>
                    {lang.label}
                  </option>
                ))}
              </select>
              <Globe size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            </div>

            {/* Voice Mode Toggle Button */}
            <button
              type="button"
              onClick={handleVoiceToggle}
              disabled={disabled}
              className={`p-2.5 rounded-lg transition-colors ${
                voiceModeActive
                  ? 'bg-red-500 hover:bg-red-600'
                  : 'bg-blue-500 hover:bg-blue-600'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={voiceModeActive ? "Exit voice mode" : "Start voice mode"}
            >
              {voiceModeActive ? (
                <MicOff size={18} />
              ) : (
                <Mic size={18} />
              )}
            </button>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!message.trim() || disabled || voiceModeActive}
              className="p-2.5 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
        <p className="text-center text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line • Select language and click mic for voice mode
        </p>
      </div>
    </div>
  )
}

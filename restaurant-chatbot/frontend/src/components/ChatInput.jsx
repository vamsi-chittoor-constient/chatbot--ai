import React, { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff, Loader2 } from 'lucide-react'

export const ChatInput = ({
  onSend,
  disabled,
  // Voice props
  isRecording = false,
  isProcessing = false,
  onStartRecording = () => {},
  onStopRecording = () => {},
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
    if (isRecording) {
      onStopRecording()
    } else {
      onStartRecording()
    }
  }

  return (
    <div className="bg-chat-secondary border-t border-chat-border p-4">
      <div className="max-w-3xl mx-auto">
        {/* Language Selector (only show when not recording/processing) */}
        {!isRecording && !isProcessing && (
          <div className="flex items-center gap-2 mb-2">
            <label htmlFor="language" className="text-sm text-gray-400">Voice Language:</label>
            <select
              id="language"
              value={selectedLanguage}
              onChange={(e) => onLanguageChange(e.target.value)}
              className="bg-chat-bg border border-chat-border rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-accent"
            >
              <option value="English">English</option>
              <option value="Hindi">Hindi</option>
              <option value="Hinglish">Hinglish</option>
            </select>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <div className="flex-1 flex items-end bg-chat-bg border border-chat-border rounded-xl p-1 focus-within:border-accent transition-colors">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isRecording ? "Listening..." : isProcessing ? "Processing..." : "Type your message..."}
              disabled={disabled || isRecording || isProcessing}
              rows={1}
              className="flex-1 bg-transparent text-white text-[15px] px-3 py-2.5 resize-none focus:outline-none placeholder-gray-500 disabled:opacity-50"
            />

            {/* Voice Mode Button */}
            <button
              type="button"
              onClick={handleVoiceToggle}
              disabled={disabled || isProcessing}
              className={`p-2.5 rounded-lg transition-colors ${
                isRecording
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                  : isProcessing
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={isRecording ? "Stop recording" : isProcessing ? "Processing..." : "Start voice chat"}
            >
              {isProcessing ? (
                <Loader2 size={18} className="animate-spin" />
              ) : isRecording ? (
                <MicOff size={18} />
              ) : (
                <Mic size={18} />
              )}
            </button>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!message.trim() || disabled || isRecording || isProcessing}
              className="p-2.5 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
        <p className="text-center text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line • Click mic for voice chat
        </p>
      </div>
    </div>
  )
}

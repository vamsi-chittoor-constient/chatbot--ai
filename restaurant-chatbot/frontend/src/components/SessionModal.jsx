import React from 'react'
import { MessageSquare, RefreshCw } from 'lucide-react'

export const SessionModal = ({ onContinue, onNewChat }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-chat-secondary border border-chat-border rounded-lg p-6 max-w-sm mx-4 shadow-xl">
        <h2 className="text-lg font-semibold mb-3 text-center">
          Welcome Back!
        </h2>
        <p className="text-gray-400 text-sm mb-6 text-center">
          You have a recent conversation. Would you like to continue where you left off?
        </p>
        <div className="flex flex-col gap-3">
          <button
            onClick={onContinue}
            className="flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 text-white py-3 px-4 rounded-lg transition-colors"
          >
            <MessageSquare size={18} />
            Continue Conversation
          </button>
          <button
            onClick={onNewChat}
            className="flex items-center justify-center gap-2 bg-chat-tertiary hover:bg-gray-600 text-gray-200 py-3 px-4 rounded-lg transition-colors border border-chat-border"
          >
            <RefreshCw size={18} />
            Start Fresh
          </button>
        </div>
      </div>
    </div>
  )
}

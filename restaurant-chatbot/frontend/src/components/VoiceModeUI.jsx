import React from 'react'
import { Mic, MicOff, Volume2, Loader2 } from 'lucide-react'

export const VoiceModeUI = ({
  isRecording,
  isProcessing,
  isUserSpeaking,
  isAISpeaking,
  onExitVoiceMode,
  transcript = '',
  responseText = ''
}) => {
  // Determine current state
  const getCurrentState = () => {
    if (isAISpeaking) return 'speaking'
    if (isProcessing) return 'processing'
    if (isUserSpeaking) return 'user-speaking'
    if (isRecording) return 'listening'
    return 'idle'
  }

  const state = getCurrentState()

  const stateConfig = {
    listening: {
      icon: <Mic size={48} className="text-gray-400" />,
      title: '👂 Listening...',
      subtitle: 'Start speaking',
      bgColor: 'bg-gray-800',
      borderColor: 'border-gray-600'
    },
    'user-speaking': {
      icon: <Mic size={48} className="text-accent animate-pulse" />,
      title: '🗣️ Listening',
      subtitle: 'Speak naturally, I\'ll detect when you finish',
      bgColor: 'bg-accent/10',
      borderColor: 'border-accent'
    },
    processing: {
      icon: <Loader2 size={48} className="text-yellow-500 animate-spin" />,
      title: '⏳ Processing',
      subtitle: 'Understanding your request...',
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500'
    },
    speaking: {
      icon: <Volume2 size={48} className="text-green-500 animate-pulse" />,
      title: '🤖 Speaking',
      subtitle: 'Playing response...',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500'
    },
    idle: {
      icon: <Mic size={48} className="text-gray-500" />,
      title: 'Ready',
      subtitle: 'Waiting...',
      bgColor: 'bg-gray-800',
      borderColor: 'border-gray-600'
    }
  }

  const config = stateConfig[state]

  return (
    <div className="flex-1 flex items-center justify-center bg-chat-bg">
      <div className="max-w-md w-full mx-4">
        {/* Main Voice UI Card */}
        <div className={`${config.bgColor} border-2 ${config.borderColor} rounded-3xl p-8 transition-all duration-300`}>
          {/* Icon */}
          <div className="flex justify-center mb-6">
            <div className="p-6 rounded-full bg-gray-900/50">
              {config.icon}
            </div>
          </div>

          {/* State Text */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">
              {config.title}
            </h2>
            <p className="text-gray-400 text-sm">
              {config.subtitle}
            </p>
          </div>

          {/* Visual Indicator */}
          <div className="flex justify-center gap-2 mb-6">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className={`w-2 h-12 rounded-full transition-all ${
                  state === 'user-speaking'
                    ? 'bg-accent animate-pulse'
                    : state === 'speaking'
                    ? 'bg-green-500 animate-pulse'
                    : 'bg-gray-700'
                }`}
                style={{
                  animationDelay: `${i * 0.1}s`,
                  height: state === 'user-speaking' || state === 'speaking' ? `${20 + Math.random() * 30}px` : '12px'
                }}
              />
            ))}
          </div>

          {/* Transcript Display */}
          {(transcript || responseText) && (
            <div className="mb-6 space-y-3">
              {transcript && (
                <div className="bg-gray-900/70 rounded-xl p-4 border border-gray-700">
                  <div className="text-xs text-gray-500 mb-1">You said:</div>
                  <div className="text-white text-sm">{transcript}</div>
                </div>
              )}
              {responseText && (
                <div className="bg-green-900/30 rounded-xl p-4 border border-green-700">
                  <div className="text-xs text-green-500 mb-1">AI Response:</div>
                  <div className="text-white text-sm">{responseText}</div>
                </div>
              )}
            </div>
          )}

          {/* Instructions */}
          <div className="text-center text-xs text-gray-500 mb-6 space-y-1">
            <p>🎤 Voice Mode Active</p>
            <p>🧠 Powered by Silero VAD (Server-side ML speech detection)</p>
            <p>Continuous conversation - no need to click</p>
          </div>

          {/* Exit Button */}
          <button
            onClick={onExitVoiceMode}
            className="w-full py-3 px-4 bg-red-600/20 hover:bg-red-600/30 border border-red-600 rounded-xl text-red-500 font-medium transition-colors flex items-center justify-center gap-2"
          >
            <MicOff size={18} />
            Exit Voice Mode
          </button>
        </div>

        {/* Help Text Below */}
        <div className="mt-4 text-center text-xs text-gray-600">
          <p>Voice conversation continues automatically</p>
          <p className="mt-1">Speak → AI responds → Listen → Repeat</p>
        </div>
      </div>
    </div>
  )
}

import React from 'react';
import { Mic, MicOff, Volume2, X, Loader2 } from 'lucide-react';

export function VoiceModeBanner({
  isRecording,
  isProcessing,
  isUserSpeaking,
  isAISpeaking,
  onExitVoiceMode
}) {
  // Determine current state for display
  const getStateInfo = () => {
    if (isProcessing) {
      return { text: 'Processing...', icon: Loader2, color: 'text-yellow-400', animate: true };
    }
    if (isAISpeaking) {
      return { text: 'AI Speaking', icon: Volume2, color: 'text-green-400', animate: false };
    }
    if (isUserSpeaking) {
      return { text: 'Listening...', icon: Mic, color: 'text-red-400', animate: true };
    }
    if (isRecording) {
      return { text: 'Voice Mode Active', icon: Mic, color: 'text-blue-400', animate: false };
    }
    return { text: 'Connecting...', icon: MicOff, color: 'text-gray-400', animate: false };
  };

  const { text, icon: Icon, color, animate } = getStateInfo();

  return (
    <div className="bg-gradient-to-r from-indigo-900/90 to-purple-900/90 border-b border-purple-500/30 px-4 py-2">
      <div className="flex items-center justify-between max-w-3xl mx-auto">
        {/* Left: Voice status */}
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-full ${isUserSpeaking ? 'bg-red-500/20' : 'bg-white/10'}`}>
            <Icon
              size={18}
              className={`${color} ${animate ? 'animate-pulse' : ''}`}
            />
          </div>
          <span className="text-sm font-medium text-white/90">{text}</span>

          {/* Audio visualizer dots */}
          {(isUserSpeaking || isAISpeaking) && (
            <div className="flex items-center gap-1 ml-2">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className={`w-1 rounded-full ${isUserSpeaking ? 'bg-red-400' : 'bg-green-400'}`}
                  style={{
                    height: `${8 + Math.random() * 12}px`,
                    animation: 'pulse 0.5s ease-in-out infinite',
                    animationDelay: `${i * 0.1}s`
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Right: Exit button */}
        <button
          onClick={onExitVoiceMode}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition-colors text-sm"
        >
          <X size={14} />
          <span>Exit Voice</span>
        </button>
      </div>
    </div>
  );
}

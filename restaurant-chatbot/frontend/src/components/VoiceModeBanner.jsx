import React from 'react';
import { Mic, MicOff, Volume2, X, Loader2, Square } from 'lucide-react';

export function VoiceModeBanner({
  isRecording,
  isProcessing,
  isUserSpeaking,
  isAISpeaking,
  onExitVoiceMode,
  onStopAgent
}) {
  // Determine current state for display
  // Priority: Processing > AI Speaking > User Speaking > Idle Recording > Connecting
  const getStateInfo = () => {
    if (isProcessing && !isAISpeaking) {
      return {
        text: 'Processing...',
        subtext: 'Please wait',
        icon: Loader2,
        color: 'text-yellow-400',
        animate: true,
        bgGradient: 'from-yellow-600 to-orange-600',
        showStopButton: false,
        micMuted: true,
      };
    }
    if (isAISpeaking) {
      return {
        text: 'Agent Speaking',
        subtext: 'Mic muted - tap Stop to interrupt',
        icon: Volume2,
        color: 'text-green-400',
        animate: true,
        bgGradient: 'from-green-600 to-emerald-600',
        showStopButton: true,
        micMuted: true,
      };
    }
    if (isUserSpeaking) {
      return {
        text: 'Listening...',
        subtext: 'Speak now',
        icon: Mic,
        color: 'text-red-400',
        animate: true,
        bgGradient: 'from-red-600 to-orange-600',
        showStopButton: false,
        micMuted: false,
      };
    }
    if (isRecording) {
      return {
        text: 'Voice Mode Active',
        subtext: 'Start speaking...',
        icon: Mic,
        color: 'text-blue-400',
        animate: false,
        bgGradient: 'from-blue-600 to-indigo-600',
        showStopButton: false,
        micMuted: false,
      };
    }
    return {
      text: 'Connecting...',
      subtext: '',
      icon: MicOff,
      color: 'text-gray-400',
      animate: false,
      bgGradient: 'from-gray-600 to-gray-700',
      showStopButton: false,
      micMuted: false,
    };
  };

  const { text, subtext, icon: Icon, color, animate, bgGradient, showStopButton, micMuted } = getStateInfo();

  return (
    <div className={`bg-gradient-to-r ${bgGradient} border-b border-white/10 px-4 py-3 shadow-md`}>
      <div className="flex items-center justify-between max-w-3xl mx-auto">
        {/* Left: Voice status */}
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-full ${isUserSpeaking ? 'bg-white/30' : 'bg-white/10'} relative`}>
            <Icon
              size={20}
              className={`text-white ${animate ? 'animate-pulse' : ''}`}
            />
            {/* Mic muted indicator */}
            {micMuted && (
              <div className="absolute -bottom-0.5 -right-0.5 bg-red-500 rounded-full w-3 h-3 flex items-center justify-center">
                <MicOff size={8} className="text-white" />
              </div>
            )}
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-white">{text}</span>
            {subtext && (
              <span className="text-xs text-white/70">{subtext}</span>
            )}
          </div>

          {/* Audio visualizer dots */}
          {(isUserSpeaking || isAISpeaking) && (
            <div className="flex items-center gap-1 ml-2">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="w-1 rounded-full bg-white"
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

        {/* Right: Action buttons */}
        <div className="flex items-center gap-2">
          {/* Stop Agent button - shown when AI is speaking */}
          {showStopButton && onStopAgent && (
            <button
              onClick={onStopAgent}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/80 hover:bg-red-500 text-white hover:shadow-lg transition-all text-xs font-semibold"
            >
              <Square size={12} fill="white" />
              <span>Stop</span>
            </button>
          )}

          {/* Exit button */}
          <button
            onClick={onExitVoiceMode}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/20 hover:bg-white/30 text-white hover:shadow-lg transition-all text-sm font-medium"
          >
            <X size={16} />
            <span>Exit</span>
          </button>
        </div>
      </div>
    </div>
  );
}

import React from 'react'

export const QuickReplies = ({ options, onSelect }) => {
  if (!options || options.length === 0) return null

  const handleClick = (option) => {
    const value = typeof option === 'string' ? option : (option.value || option.label || option.text)
    onSelect(value)
  }

  return (
    <div className="flex flex-wrap gap-2 animate-fadeIn">
      {options.map((option, index) => {
        const label = typeof option === 'string' ? option : (option.label || option.text || option)
        return (
          <button
            key={index}
            onClick={() => handleClick(option)}
            className="px-4 py-2 rounded-full border border-chat-border text-sm text-gray-300 hover:bg-accent hover:border-accent hover:text-white transition-all"
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}

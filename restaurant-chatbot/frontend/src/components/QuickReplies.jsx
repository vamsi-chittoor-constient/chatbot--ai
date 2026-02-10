import React from 'react'

export const QuickReplies = ({ options, onSelect }) => {
  if (!options || options.length === 0) return null

  const handleClick = (option) => {
    const value = typeof option === 'string' ? option : (option.action || option.value || option.label || option.text)
    onSelect(value)
  }

  return (
    <div className="flex flex-wrap gap-2 animate-fadeIn mt-3">
      {options.map((option, index) => {
        const label = typeof option === 'string' ? option : (option.label || option.text || option)
        return (
          <button
            key={index}
            onClick={() => handleClick(option)}
            className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-all shadow-sm hover:shadow-md transform hover:scale-105"
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}

import { useState } from 'react'
import { Calendar, Clock, Users, Loader2 } from 'lucide-react'

export const BookingFormCard = ({ data, onSubmit }) => {
  const { party_sizes = [1, 2, 3, 4, 5, 6, 7, 8], restaurant_name = '' } = data

  // Default date = tomorrow
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  const defaultDate = tomorrow.toISOString().split('T')[0]

  const [selectedDate, setSelectedDate] = useState(defaultDate)
  const [selectedTime, setSelectedTime] = useState('19:00')
  const [selectedPartySize, setSelectedPartySize] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  // Min date = today
  const today = new Date().toISOString().split('T')[0]

  // Format display
  const formatDate = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00')
    return d.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })
  }

  const formatTime = (timeStr) => {
    const [h, m] = timeStr.split(':')
    const hour = parseInt(h)
    const ampm = hour >= 12 ? 'PM' : 'AM'
    const h12 = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
    return `${h12}:${m} ${ampm}`
  }

  const handleSubmit = () => {
    if (!selectedDate || !selectedTime || !selectedPartySize) return
    setSubmitted(true)
    onSubmit?.('booking_intake', {
      date: selectedDate,
      time: formatTime(selectedTime),
      party_size: selectedPartySize,
    })
  }

  if (submitted) {
    return (
      <div className="mb-6 animate-fadeIn">
        <div className="bg-chat-assistant rounded-2xl p-6 border border-gray-700/50 text-center">
          <div className="w-12 h-12 bg-indigo-600/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
          </div>
          <p className="text-white font-medium">Reserving your table...</p>
          <p className="text-gray-400 text-sm mt-1">
            {selectedPartySize} guests on {formatDate(selectedDate)} at {formatTime(selectedTime)}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mb-6 animate-fadeIn">
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-t-2xl p-5 text-white">
        <h3 className="text-lg font-bold flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Book a Table
          {restaurant_name && <span className="text-indigo-200 text-sm font-normal">at {restaurant_name}</span>}
        </h3>
      </div>
      <div className="bg-chat-assistant rounded-b-2xl p-5 border border-gray-700/50 space-y-5">
        {/* Party Size */}
        <div>
          <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
            <Users size={14} /> How many guests?
          </p>
          <div className="flex flex-wrap gap-2">
            {party_sizes.map(size => (
              <button key={size} onClick={() => setSelectedPartySize(size)}
                className={`px-4 py-2 rounded-xl font-medium transition-all ${
                  selectedPartySize === size
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                }`}>
                {size}
              </button>
            ))}
          </div>
        </div>

        {/* Date Picker */}
        <div>
          <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
            <Calendar size={14} /> Select date
          </p>
          <input
            type="date"
            value={selectedDate}
            min={today}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="w-full bg-gray-700/50 text-white border border-gray-600 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors"
          />
          {selectedDate && (
            <p className="text-indigo-400 text-xs mt-1">{formatDate(selectedDate)}</p>
          )}
        </div>

        {/* Time Picker */}
        <div>
          <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
            <Clock size={14} /> Select time
          </p>
          <input
            type="time"
            value={selectedTime}
            onChange={(e) => setSelectedTime(e.target.value)}
            className="w-full bg-gray-700/50 text-white border border-gray-600 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors"
          />
          {selectedTime && (
            <p className="text-indigo-400 text-xs mt-1">{formatTime(selectedTime)}</p>
          )}
        </div>

        {/* Submit */}
        <button onClick={handleSubmit}
          disabled={!selectedDate || !selectedTime || !selectedPartySize}
          className={`w-full py-3 rounded-xl font-medium transition-all ${
            selectedDate && selectedTime && selectedPartySize
              ? 'bg-indigo-600 hover:bg-indigo-700 text-white hover:scale-[1.02] active:scale-95'
              : 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
          }`}>
          Reserve Table
        </button>
      </div>
    </div>
  )
}

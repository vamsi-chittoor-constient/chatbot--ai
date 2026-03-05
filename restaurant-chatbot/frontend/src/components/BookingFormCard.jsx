import { useState } from 'react'
import { Calendar, Clock, Users } from 'lucide-react'

export const BookingFormCard = ({ data, onSubmit }) => {
  const { time_slots = [], party_sizes = [2, 4, 6, 8], restaurant_name = '' } = data

  const [selectedSlot, setSelectedSlot] = useState(null)
  const [selectedPartySize, setSelectedPartySize] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  // Group time slots by date_label
  const slotsByDate = time_slots.reduce((acc, slot) => {
    const key = slot.date_label || slot.date
    if (!acc[key]) acc[key] = []
    acc[key].push(slot)
    return acc
  }, {})

  const handleSubmit = () => {
    if (!selectedSlot || !selectedPartySize) return
    setSubmitted(true)
    onSubmit?.('booking_intake', {
      date: selectedSlot.date,
      time: selectedSlot.time,
      party_size: selectedPartySize,
    })
  }

  if (submitted) {
    return (
      <div className="mb-6 animate-fadeIn">
        <div className="bg-chat-assistant rounded-2xl p-6 border border-gray-700/50 text-center">
          <p className="text-gray-300">Checking availability for {selectedPartySize} guests on {selectedSlot.date_label} at {selectedSlot.time}...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="mb-6 animate-fadeIn">
      {/* Header */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-t-2xl p-5 text-white">
        <div className="flex items-center gap-3">
          <Calendar className="w-6 h-6" />
          <div>
            <h3 className="text-lg font-bold">Book a Table</h3>
            {restaurant_name && <p className="text-indigo-100 text-sm">{restaurant_name}</p>}
          </div>
        </div>
      </div>

      <div className="bg-chat-assistant rounded-b-2xl p-5 border border-gray-700/50 space-y-5">
        {/* Party Size */}
        <div>
          <label className="text-gray-400 text-sm flex items-center gap-2 mb-3">
            <Users size={14} /> How many guests?
          </label>
          <div className="flex gap-2">
            {party_sizes.map(size => (
              <button
                key={size}
                onClick={() => setSelectedPartySize(size)}
                className={`flex-1 py-2.5 rounded-xl font-medium transition-all text-sm ${
                  selectedPartySize === size
                    ? 'bg-indigo-600 text-white border border-indigo-500'
                    : 'bg-gray-700/50 text-gray-300 border border-gray-600/50 hover:border-indigo-500/50'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
        </div>

        {/* Time Slots */}
        <div>
          <label className="text-gray-400 text-sm flex items-center gap-2 mb-3">
            <Clock size={14} /> Pick a time
          </label>
          <div className="space-y-4">
            {Object.entries(slotsByDate).map(([dateLabel, slots]) => (
              <div key={dateLabel}>
                <p className="text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">{dateLabel}</p>
                <div className="flex flex-wrap gap-2">
                  {slots.map((slot, i) => (
                    <button
                      key={i}
                      onClick={() => setSelectedSlot(slot)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                        selectedSlot === slot
                          ? 'bg-indigo-600 text-white border border-indigo-500'
                          : 'bg-gray-700/50 text-gray-300 border border-gray-600/50 hover:border-indigo-500/50'
                      }`}
                    >
                      {slot.time}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!selectedSlot || !selectedPartySize}
          className={`w-full py-3 rounded-xl font-semibold transition-all ${
            selectedSlot && selectedPartySize
              ? 'bg-indigo-600 hover:bg-indigo-700 text-white hover:scale-[1.02] active:scale-[0.98]'
              : 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
          }`}
        >
          Check Availability
        </button>
      </div>
    </div>
  )
}

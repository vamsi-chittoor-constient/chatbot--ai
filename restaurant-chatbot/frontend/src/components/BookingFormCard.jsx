import { useState } from 'react'
import { Calendar, Clock, Users } from 'lucide-react'

export const BookingFormCard = ({ data, onSubmit }) => {
  const { time_slots = [], party_sizes = [2, 4, 6, 8], restaurant_name = '' } = data
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [selectedPartySize, setSelectedPartySize] = useState(null)
  const [submitted, setSubmitted] = useState(false)

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
          <div className="w-12 h-12 bg-indigo-600/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <Calendar className="w-6 h-6 text-indigo-400" />
          </div>
          <p className="text-white font-medium">Booking request submitted!</p>
          <p className="text-gray-400 text-sm mt-1">
            {selectedPartySize} guests on {selectedSlot.date} at {selectedSlot.time}
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
                {size} {size === 1 ? 'guest' : 'guests'}
              </button>
            ))}
          </div>
        </div>

        {/* Time Slots grouped by date */}
        <div>
          <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
            <Clock size={14} /> Pick a time
          </p>
          {Object.entries(slotsByDate).map(([dateLabel, slots]) => (
            <div key={dateLabel} className="mb-3">
              <p className="text-white text-sm font-medium mb-2">{dateLabel}</p>
              <div className="flex flex-wrap gap-2">
                {slots.map((slot, idx) => (
                  <button key={idx} onClick={() => setSelectedSlot(slot)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      selectedSlot === slot
                        ? 'bg-indigo-600 text-white'
                        : slot.available
                          ? 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                          : 'bg-gray-800/50 text-gray-600 cursor-not-allowed'
                    }`}
                    disabled={!slot.available}>
                    {slot.time}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {time_slots.length === 0 && (
            <p className="text-gray-500 text-sm">No available slots right now.</p>
          )}
        </div>

        {/* Submit */}
        <button onClick={handleSubmit}
          disabled={!selectedSlot || !selectedPartySize}
          className={`w-full py-3 rounded-xl font-medium transition-all ${
            selectedSlot && selectedPartySize
              ? 'bg-indigo-600 hover:bg-indigo-700 text-white hover:scale-[1.02] active:scale-95'
              : 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
          }`}>
          Reserve Table
        </button>
      </div>
    </div>
  )
}

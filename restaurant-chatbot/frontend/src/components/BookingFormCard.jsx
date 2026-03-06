import { useState, useMemo } from 'react'
import { Calendar, Clock, Users, Loader2, AlertCircle } from 'lucide-react'

export const BookingFormCard = ({ data, onSubmit }) => {
  const {
    party_sizes = [1, 2, 3, 4, 5, 6, 7, 8],
    restaurant_name = '',
    availability = {},
    max_party_size = 8,
  } = data

  const [selectedPartySize, setSelectedPartySize] = useState(null)
  const [selectedDate, setSelectedDate] = useState(null)
  const [selectedTime, setSelectedTime] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  // Build date options from availability keys (next 7 days)
  const dateOptions = useMemo(() => {
    const dates = Object.keys(availability).sort()
    if (dates.length === 0) {
      // Fallback: generate next 7 days if no availability data
      const result = []
      for (let i = 1; i <= 7; i++) {
        const d = new Date()
        d.setDate(d.getDate() + i)
        result.push(d.toISOString().split('T')[0])
      }
      return result
    }
    return dates
  }, [availability])

  // Has availability data from backend?
  const hasAvailability = Object.keys(availability).length > 0

  // For a given date + party size, get available time slots
  const getSlots = (dateStr, partySize) => {
    const dateData = availability[dateStr]
    if (!dateData || !dateData.slots) return {}
    const slots = {}
    for (const [time, info] of Object.entries(dateData.slots)) {
      slots[time] = {
        ...info,
        available: info.available && info.max_party >= partySize,
      }
    }
    return slots
  }

  // Check if a date has ANY available slot for the selected party size
  const isDateAvailable = (dateStr, partySize) => {
    if (!partySize) return true
    if (!hasAvailability) return true
    const slots = getSlots(dateStr, partySize)
    return Object.values(slots).some(s => s.available)
  }

  // Get time slots for the selected date + party size
  const timeSlots = useMemo(() => {
    if (!selectedDate || !selectedPartySize) return {}
    return getSlots(selectedDate, selectedPartySize)
  }, [selectedDate, selectedPartySize, availability])

  // Format helpers
  const formatDateLabel = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00')
    const today = new Date()
    const tomorrow = new Date()
    tomorrow.setDate(today.getDate() + 1)

    if (d.toDateString() === today.toDateString()) return 'Today'
    if (d.toDateString() === tomorrow.toDateString()) return 'Tomorrow'
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  }

  const formatDayOfWeek = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00')
    return d.toLocaleDateString('en-US', { weekday: 'short' })
  }

  const formatDayNum = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00')
    return d.getDate()
  }

  const formatMonth = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00')
    return d.toLocaleDateString('en-US', { month: 'short' })
  }

  // Reset downstream selections when upstream changes
  const handlePartySizeChange = (size) => {
    setSelectedPartySize(size)
    setSelectedDate(null)
    setSelectedTime(null)
  }

  const handleDateChange = (dateStr) => {
    setSelectedDate(dateStr)
    setSelectedTime(null)
  }

  const handleSubmit = () => {
    if (!selectedDate || !selectedTime || !selectedPartySize) return
    setSubmitted(true)
    onSubmit?.('booking_intake', {
      date: selectedDate,
      time: selectedTime,
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
            {selectedPartySize} guests on {formatDateLabel(selectedDate)} at {selectedTime}
          </p>
        </div>
      </div>
    )
  }

  // Count available slots for selected date
  const availableSlotCount = Object.values(timeSlots).filter(s => s.available).length
  const totalSlotCount = Object.keys(timeSlots).length

  return (
    <div className="mb-6 animate-fadeIn">
      {/* Header */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-t-2xl p-5 text-white">
        <h3 className="text-lg font-bold flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Book a Table
          {restaurant_name && <span className="text-indigo-200 text-sm font-normal">at {restaurant_name}</span>}
        </h3>
        {hasAvailability && (
          <p className="text-indigo-200 text-xs mt-1">Showing real-time availability</p>
        )}
      </div>

      <div className="bg-chat-assistant rounded-b-2xl p-5 border border-gray-700/50 space-y-5">

        {/* Step 1: Party Size */}
        <div>
          <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
            <Users size={14} /> How many guests?
          </p>
          <div className="flex flex-wrap gap-2">
            {party_sizes.map(size => (
              <button key={size} onClick={() => handlePartySizeChange(size)}
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

        {/* Step 2: Date (shown after party size) */}
        {selectedPartySize && (
          <div className="animate-fadeIn">
            <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
              <Calendar size={14} /> Select date
            </p>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {dateOptions.map(dateStr => {
                const available = isDateAvailable(dateStr, selectedPartySize)
                const isSelected = selectedDate === dateStr

                return (
                  <button
                    key={dateStr}
                    onClick={() => available && handleDateChange(dateStr)}
                    disabled={!available}
                    className={`flex-shrink-0 w-16 py-3 rounded-xl text-center transition-all ${
                      isSelected
                        ? 'bg-indigo-600 text-white'
                        : available
                          ? 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                          : 'bg-gray-800/30 text-gray-600 cursor-not-allowed'
                    }`}
                  >
                    <div className="text-[10px] uppercase">{formatDayOfWeek(dateStr)}</div>
                    <div className="text-lg font-bold">{formatDayNum(dateStr)}</div>
                    <div className="text-[10px] uppercase">{formatMonth(dateStr)}</div>
                    {!available && hasAvailability && (
                      <div className="text-[8px] text-red-400 mt-0.5">Full</div>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Step 3: Time Slots (shown after date) */}
        {selectedDate && selectedPartySize && (
          <div className="animate-fadeIn">
            <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
              <Clock size={14} /> Select time
              {hasAvailability && totalSlotCount > 0 && (
                <span className="text-xs text-gray-500">
                  ({availableSlotCount} of {totalSlotCount} slots open)
                </span>
              )}
            </p>

            {hasAvailability && totalSlotCount > 0 ? (
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 max-h-48 overflow-y-auto pr-1">
                {Object.entries(timeSlots).map(([time, info]) => {
                  const isSelected = selectedTime === time
                  return (
                    <button
                      key={time}
                      onClick={() => info.available && setSelectedTime(time)}
                      disabled={!info.available}
                      className={`px-2 py-2 rounded-xl text-sm font-medium transition-all ${
                        isSelected
                          ? 'bg-indigo-600 text-white'
                          : info.available
                            ? 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                            : 'bg-gray-800/30 text-gray-600 cursor-not-allowed line-through'
                      }`}
                    >
                      {time}
                    </button>
                  )
                })}
              </div>
            ) : (
              /* Fallback: time input if no availability data */
              <div>
                <input
                  type="time"
                  value={selectedTime || '19:00'}
                  onChange={(e) => {
                    const [h, m] = e.target.value.split(':')
                    const hour = parseInt(h)
                    const ampm = hour >= 12 ? 'PM' : 'AM'
                    const h12 = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
                    setSelectedTime(`${h12}:${m} ${ampm}`)
                  }}
                  className="w-full bg-gray-700/50 text-white border border-gray-600 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            )}

            {availableSlotCount === 0 && hasAvailability && (
              <div className="flex items-center gap-2 text-amber-400 text-xs mt-2">
                <AlertCircle size={12} />
                No available slots for {selectedPartySize} guests on this date. Try another date.
              </div>
            )}
          </div>
        )}

        {/* Summary + Submit */}
        {selectedDate && selectedTime && selectedPartySize && (
          <div className="animate-fadeIn">
            <div className="bg-gray-700/30 rounded-xl p-3 mb-3 text-sm">
              <div className="flex justify-between text-gray-300">
                <span>Guests</span>
                <span className="text-white font-medium">{selectedPartySize}</span>
              </div>
              <div className="flex justify-between text-gray-300 mt-1">
                <span>Date</span>
                <span className="text-white font-medium">{formatDateLabel(selectedDate)}</span>
              </div>
              <div className="flex justify-between text-gray-300 mt-1">
                <span>Time</span>
                <span className="text-white font-medium">{selectedTime}</span>
              </div>
            </div>

            <button onClick={handleSubmit}
              className="w-full py-3 rounded-xl font-medium transition-all bg-indigo-600 hover:bg-indigo-700 text-white hover:scale-[1.02] active:scale-95">
              Reserve Table
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

import { useState, useMemo } from 'react'
import { Calendar, Clock, Users, Loader2, AlertCircle } from 'lucide-react'

export const BookingFormCard = ({ data, onSubmit }) => {
  const {
    party_sizes = [1, 2, 3, 4, 5, 6, 7, 8],
    restaurant_name = '',
    availability = {},
    max_party_size = 8,
  } = data

  const [selectedDate, setSelectedDate] = useState(null)
  const [selectedPartySize, setSelectedPartySize] = useState(null)
  const [selectedTime, setSelectedTime] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  // Quick-select dates from availability (next 7 days)
  const quickDates = useMemo(() => {
    const dates = Object.keys(availability).sort()
    if (dates.length === 0) {
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

  // Min date for date input = tomorrow
  const minDate = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() + 1)
    return d.toISOString().split('T')[0]
  }, [])

  const hasAvailability = Object.keys(availability).length > 0
  const isDateInAvailability = selectedDate && availability[selectedDate]

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

  // Available party sizes for the selected date
  const availablePartySizes = useMemo(() => {
    if (!selectedDate || !isDateInAvailability) return party_sizes
    const dateData = availability[selectedDate]
    if (!dateData || !dateData.slots) return party_sizes
    // Max party size available across all slots on this date
    const maxAvail = Math.max(...Object.values(dateData.slots).filter(s => s.available).map(s => s.max_party), 0)
    return party_sizes.filter(size => size <= maxAvail)
  }, [selectedDate, isDateInAvailability, availability, party_sizes])

  // Time slots for selected date + party size
  const timeSlots = useMemo(() => {
    if (!selectedDate || !selectedPartySize) return {}
    return getSlots(selectedDate, selectedPartySize)
  }, [selectedDate, selectedPartySize, availability])

  const availableSlotCount = Object.values(timeSlots).filter(s => s.available).length
  const totalSlotCount = Object.keys(timeSlots).length

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

  const formatDayNum = (dateStr) => new Date(dateStr + 'T00:00:00').getDate()

  const formatMonth = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00')
    return d.toLocaleDateString('en-US', { month: 'short' })
  }

  // Handlers — reset downstream when upstream changes
  const handleDateChange = (dateStr) => {
    setSelectedDate(dateStr)
    setSelectedPartySize(null)
    setSelectedTime(null)
  }

  const handlePartySizeChange = (size) => {
    setSelectedPartySize(size)
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

  return (
    <div className="mb-6 animate-fadeIn">
      {/* Header */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-t-2xl p-5 text-white">
        <h3 className="text-lg font-bold flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Book a Table
          {restaurant_name && <span className="text-indigo-200 text-sm font-normal">at {restaurant_name}</span>}
        </h3>
      </div>

      <div className="bg-chat-assistant rounded-b-2xl p-5 border border-gray-700/50 space-y-5">

        {/* Step 1: Date */}
        <div>
          <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
            <Calendar size={14} /> When would you like to dine?
          </p>

          {/* Quick-select date cards */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {quickDates.map(dateStr => {
              const isSelected = selectedDate === dateStr
              return (
                <button
                  key={dateStr}
                  onClick={() => handleDateChange(dateStr)}
                  className={`flex-shrink-0 w-16 py-3 rounded-xl text-center transition-all ${
                    isSelected
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <div className="text-[10px] uppercase">{formatDayOfWeek(dateStr)}</div>
                  <div className="text-lg font-bold">{formatDayNum(dateStr)}</div>
                  <div className="text-[10px] uppercase">{formatMonth(dateStr)}</div>
                </button>
              )
            })}
          </div>

          {/* Custom date picker */}
          <div className="mt-2">
            <p className="text-gray-500 text-xs mb-1">Or pick any date:</p>
            <input
              type="date"
              min={minDate}
              value={selectedDate || ''}
              onChange={(e) => e.target.value && handleDateChange(e.target.value)}
              className="w-full bg-gray-700/50 text-white border border-gray-600 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {selectedDate && (
            <p className="text-indigo-400 text-xs mt-1">{formatDateLabel(selectedDate)}</p>
          )}
        </div>

        {/* Step 2: Party Size (shown after date) */}
        {selectedDate && (
          <div className="animate-fadeIn">
            <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
              <Users size={14} /> How many guests?
            </p>
            <div className="flex flex-wrap gap-2">
              {party_sizes.map(size => {
                const isAvailable = availablePartySizes.includes(size)
                return (
                  <button key={size}
                    onClick={() => isAvailable && handlePartySizeChange(size)}
                    disabled={!isAvailable}
                    className={`px-4 py-2 rounded-xl font-medium transition-all ${
                      selectedPartySize === size
                        ? 'bg-indigo-600 text-white'
                        : isAvailable
                          ? 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                          : 'bg-gray-800/30 text-gray-600 cursor-not-allowed'
                    }`}>
                    {size}
                  </button>
                )
              })}
            </div>
            {isDateInAvailability && availablePartySizes.length < party_sizes.length && (
              <p className="text-gray-500 text-xs mt-1">Some sizes unavailable on this date</p>
            )}
          </div>
        )}

        {/* Step 3: Time Slots (shown after date + party size) */}
        {selectedDate && selectedPartySize && (
          <div className="animate-fadeIn">
            <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
              <Clock size={14} /> Select time
              {isDateInAvailability && totalSlotCount > 0 && (
                <span className="text-xs text-gray-500">
                  ({availableSlotCount} of {totalSlotCount} slots open)
                </span>
              )}
            </p>

            {isDateInAvailability && totalSlotCount > 0 ? (
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
              /* Fallback: time input for custom dates without pre-queried availability */
              <div>
                <input
                  type="time"
                  value={selectedTime ? '' : '19:00'}
                  onChange={(e) => {
                    const [h, m] = e.target.value.split(':')
                    const hour = parseInt(h)
                    const ampm = hour >= 12 ? 'PM' : 'AM'
                    const h12 = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
                    setSelectedTime(`${h12}:${m} ${ampm}`)
                  }}
                  className="w-full bg-gray-700/50 text-white border border-gray-600 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors"
                />
                <p className="text-gray-500 text-xs mt-1">Availability will be checked when you reserve</p>
              </div>
            )}

            {availableSlotCount === 0 && isDateInAvailability && (
              <div className="flex items-center gap-2 text-amber-400 text-xs mt-2">
                <AlertCircle size={12} />
                No slots for {selectedPartySize} guests on this date. Try another date or fewer guests.
              </div>
            )}
          </div>
        )}

        {/* Summary + Submit */}
        {selectedDate && selectedTime && selectedPartySize && (
          <div className="animate-fadeIn">
            <div className="bg-gray-700/30 rounded-xl p-3 mb-3 text-sm">
              <div className="flex justify-between text-gray-300">
                <span>Date</span>
                <span className="text-white font-medium">{formatDateLabel(selectedDate)}</span>
              </div>
              <div className="flex justify-between text-gray-300 mt-1">
                <span>Guests</span>
                <span className="text-white font-medium">{selectedPartySize}</span>
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

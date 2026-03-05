import { CheckCircle, Calendar, Clock, Users, MapPin, Hash } from 'lucide-react'

export const BookingConfirmationCard = ({ data, onQuickReply }) => {
  const {
    confirmation_code,
    guest_name,
    party_size,
    booking_date,
    booking_time,
    table_number,
    table_location,
    quick_replies = [],
  } = data

  return (
    <div className="mb-6 animate-fadeIn">
      {/* Success Header */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-t-2xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
            <CheckCircle className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-xl font-bold">Reservation Confirmed!</h3>
            <p className="text-indigo-100 text-sm">Your table has been reserved</p>
          </div>
        </div>
      </div>

      {/* Booking Details */}
      <div className="bg-chat-assistant rounded-b-2xl p-6 border border-gray-700/50">
        <div className="space-y-3 mb-6">
          <div className="flex justify-between items-center py-2 border-b border-gray-700/30">
            <span className="text-gray-400 text-sm flex items-center gap-2"><Hash size={14} /> Confirmation</span>
            <span className="font-mono font-bold text-indigo-400">{confirmation_code}</span>
          </div>
          {guest_name && (
            <div className="flex justify-between items-center py-2 border-b border-gray-700/30">
              <span className="text-gray-400 text-sm">Guest Name</span>
              <span className="font-medium text-white">{guest_name}</span>
            </div>
          )}
          <div className="flex justify-between items-center py-2 border-b border-gray-700/30">
            <span className="text-gray-400 text-sm flex items-center gap-2"><Calendar size={14} /> Date</span>
            <span className="font-medium text-white">{booking_date}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-700/30">
            <span className="text-gray-400 text-sm flex items-center gap-2"><Clock size={14} /> Time</span>
            <span className="font-medium text-white">{booking_time}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-700/30">
            <span className="text-gray-400 text-sm flex items-center gap-2"><Users size={14} /> Guests</span>
            <span className="font-medium text-white">{party_size}</span>
          </div>
          <div className="flex justify-between items-center py-2">
            <span className="text-gray-400 text-sm flex items-center gap-2"><MapPin size={14} /> Table</span>
            <span className="font-medium text-white">
              Table {table_number}{table_location ? ` - ${table_location}` : ''}
            </span>
          </div>
        </div>

        {/* Quick Replies */}
        {quick_replies && quick_replies.length > 0 && (
          <div className="space-y-2">
            <p className="text-gray-400 text-sm mb-3">What would you like to do next?</p>
            <div className="flex flex-wrap gap-2">
              {quick_replies.map((reply, index) => (
                <button
                  key={index}
                  onClick={() => onQuickReply?.(reply.action)}
                  className="flex-1 min-w-[140px] bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-white px-4 py-3 rounded-xl font-medium transition-all hover:scale-105 active:scale-95"
                >
                  {reply.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

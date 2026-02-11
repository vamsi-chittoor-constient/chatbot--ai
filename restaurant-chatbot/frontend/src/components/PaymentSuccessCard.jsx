import { CheckCircle } from 'lucide-react'

export const PaymentSuccessCard = ({ data, onQuickReply }) => {
  const { order_number, amount, payment_id, order_type, quick_replies = [] } = data

  return (
    <div className="mb-6 animate-fadeIn">
      {/* Success Header */}
      <div className="bg-gradient-to-br from-green-600 to-emerald-700 rounded-t-2xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
            <CheckCircle className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-xl font-bold">Payment Successful!</h3>
            <p className="text-green-100 text-sm">Your order has been confirmed</p>
          </div>
        </div>
      </div>

      {/* Order Details */}
      <div className="bg-chat-assistant rounded-b-2xl p-6 border border-gray-700/50">
        <div className="space-y-3 mb-6">
          <div className="flex justify-between items-center py-2 border-b border-gray-700/30">
            <span className="text-gray-400 text-sm">Order Number</span>
            <span className="font-semibold text-white">{order_number}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-700/30">
            <span className="text-gray-400 text-sm">Amount Paid</span>
            <span className="font-bold text-green-400 text-lg">₹{amount}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-700/30">
            <span className="text-gray-400 text-sm">Order Type</span>
            <span className="font-medium text-white">Takeaway</span>
          </div>
          {payment_id && (
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-400 text-sm">Payment ID</span>
              <span className="font-mono text-xs text-gray-300">{payment_id}</span>
            </div>
          )}
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
                  className="flex-1 min-w-[140px] bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 text-white px-4 py-3 rounded-xl font-medium transition-all hover:scale-105 active:scale-95"
                >
                  {reply.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Confirmation Message */}
        <div className="mt-6 p-4 bg-green-600/10 border border-green-500/30 rounded-xl">
          <p className="text-sm text-green-300">
            ✓ You will receive a confirmation SMS shortly with your order details.
          </p>
        </div>
      </div>
    </div>
  )
}

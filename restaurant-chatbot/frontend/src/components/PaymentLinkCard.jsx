import React from 'react'
import { ExternalLink, Clock, Shield } from 'lucide-react'

export function PaymentLinkCard({ data }) {
  const { payment_link, amount, expires_at } = data

  const formattedExpiry = expires_at
    ? new Date(expires_at).toLocaleString()
    : ''

  return (
    <div className="w-full max-w-sm bg-chat-secondary rounded-2xl overflow-hidden shadow-lg border border-chat-border my-2 animate-fade-in-up">
      {/* Header */}
      <div className="bg-chat-tertiary px-5 py-4 border-b border-chat-border">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="font-semibold text-white/90 text-lg">Complete Payment</h3>
            <p className="text-sm text-gray-400 mt-1">Secure online payment</p>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold text-white tracking-tight">
              ₹{amount}
            </span>
          </div>
        </div>
      </div>

      {/* Pay Button */}
      <div className="px-5 py-5">
        <a
          href={payment_link}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accent/90 text-white font-semibold py-3.5 px-6 rounded-xl transition-all duration-200 shadow-md hover:shadow-lg"
        >
          <ExternalLink size={18} />
          Pay ₹{amount} Now
        </a>
      </div>

      {/* Footer */}
      <div className="border-t border-chat-border px-4 py-3 bg-chat-tertiary">
        <div className="flex items-center justify-between text-xs text-gray-500">
          {formattedExpiry && (
            <span className="flex items-center gap-1">
              <Clock size={12} />
              Expires: {formattedExpiry}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Shield size={12} />
            Powered by Razorpay
          </span>
        </div>
      </div>
    </div>
  )
}

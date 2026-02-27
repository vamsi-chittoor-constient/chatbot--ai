import React from 'react'
import { ExternalLink, Clock, Shield } from 'lucide-react'

export function PaymentLinkCard({ data }) {
  const { payment_link, amount, expires_at } = data

  const formattedExpiry = expires_at
    ? new Date(expires_at).toLocaleString()
    : ''

  return (
    <div className="w-full max-w-sm bg-gradient-to-br from-red-50 to-orange-50 border-2 border-red-200 rounded-xl shadow-sm overflow-hidden my-3 animate-fade-in-up">
      {/* Header */}
      <div className="px-5 py-4">
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="font-semibold text-gray-800 text-lg">Complete Payment</h3>
            <p className="text-sm text-gray-600 mt-1">Secure online payment</p>
          </div>
          <div className="text-right">
            <span className="text-3xl font-bold text-red-600 tracking-tight">
              ₹{amount}
            </span>
          </div>
        </div>

        {/* Pay Button */}
        <a
          href={payment_link}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white font-semibold py-3.5 px-6 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
        >
          <Shield size={18} />
          Pay ₹{amount} Now with Razorpay
        </a>
      </div>

      {/* Footer */}
      {formattedExpiry && (
        <div className="border-t border-red-200 px-5 py-3 bg-red-50/50">
          <div className="flex items-center justify-center text-xs text-gray-600">
            <Clock size={12} className="mr-1" />
            Expires: {formattedExpiry}
          </div>
        </div>
      )}
    </div>
  )
}

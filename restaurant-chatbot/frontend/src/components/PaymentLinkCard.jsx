import React from 'react'
import { Clock, Shield } from 'lucide-react'

export function PaymentLinkCard({ data }) {
  const { payment_link, amount, expires_at, subtotal, packaging_charges, dine_in_charge, order_type } = data

  const formattedExpiry = expires_at
    ? new Date(expires_at).toLocaleString()
    : ''

  const hasChargesBreakdown = subtotal != null && subtotal !== amount

  return (
    <div className="w-full max-w-sm bg-gradient-to-br from-red-50 to-orange-50 border-2 border-red-200 rounded-xl shadow-sm overflow-hidden my-3 animate-fade-in-up">
      {/* Header */}
      <div className="px-5 py-4">
        <h3 className="font-semibold text-gray-800 text-lg">Complete Payment</h3>
        <p className="text-sm text-gray-600 mt-1">Secure online payment</p>

        {/* Charges breakdown */}
        {hasChargesBreakdown && (
          <div className="mt-3 space-y-1.5 text-sm">
            <div className="flex justify-between text-gray-700">
              <span>Subtotal</span>
              <span>Rs.{Number(subtotal).toFixed(0)}</span>
            </div>
            {packaging_charges > 0 && (
              <div className="flex justify-between text-gray-600">
                <span>Packaging charges</span>
                <span>Rs.{Number(packaging_charges).toFixed(0)}</span>
              </div>
            )}
            {dine_in_charge > 0 && (
              <div className="flex justify-between text-gray-600">
                <span>Service charge</span>
                <span>Rs.{Number(dine_in_charge).toFixed(0)}</span>
              </div>
            )}
            <div className="flex justify-between font-bold text-gray-900 border-t border-red-200 pt-1.5">
              <span>Total</span>
              <span>Rs.{Number(amount).toFixed(0)}</span>
            </div>
          </div>
        )}

        {/* Simple total when no breakdown */}
        {!hasChargesBreakdown && (
          <div className="mt-3 text-right">
            <span className="text-3xl font-bold text-red-600 tracking-tight">
              ₹{amount}
            </span>
          </div>
        )}

        {/* Pay Button */}
        <a
          href={payment_link}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white font-semibold py-3.5 px-6 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
        >
          <Shield size={18} />
          Pay ₹{Number(amount).toFixed(0)} Now with Razorpay
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

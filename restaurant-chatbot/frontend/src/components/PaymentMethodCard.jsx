import React from 'react'
import { CreditCard, ExternalLink } from 'lucide-react'

// Payment Method Card — shows a "Complete Payment" button linking to the payment page.
// The actual method selection (Online/Cash/Card) happens on the standalone payment page.
export function PaymentMethodCard({ data, sessionId }) {
    const { amount, currency, order_id } = data

    const paymentUrl = `/payment/${encodeURIComponent(order_id)}?sid=${encodeURIComponent(sessionId || '')}`

    return (
        <div className="w-full max-w-sm bg-chat-secondary rounded-2xl overflow-hidden shadow-lg border border-chat-border my-2 animate-fade-in-up">
            {/* Header */}
            <div className="bg-chat-tertiary px-5 py-4 border-b border-chat-border">
                <div className="flex justify-between items-start">
                    <div>
                        <h3 className="font-semibold text-white/90 text-lg">Payment</h3>
                        <p className="text-sm text-gray-400 mt-1">Order {order_id}</p>
                    </div>
                    <div className="text-right">
                        <span className="text-2xl font-bold text-white tracking-tight">
                            {currency || '₹'}{amount}
                        </span>
                    </div>
                </div>
            </div>

            {/* CTA */}
            <div className="px-5 py-5">
                <a
                    href={paymentUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accent/80 text-white font-semibold py-3.5 px-6 rounded-xl transition-all duration-200 shadow-md hover:shadow-lg"
                >
                    <CreditCard size={18} />
                    Complete Payment
                    <ExternalLink size={14} className="ml-1 opacity-70" />
                </a>
                <p className="text-xs text-gray-500 text-center mt-3">
                    Choose your payment method on the next page
                </p>
            </div>
        </div>
    )
}

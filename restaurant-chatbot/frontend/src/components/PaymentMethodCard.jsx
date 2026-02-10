import React, { useState } from 'react'
import { CreditCard, Wallet, Smartphone, CheckCircle, ChevronRight, QrCode } from 'lucide-react'

// Generic Payment Method Card
// Supports: card, upi, wallet, netbanking
export function PaymentMethodCard({ data, onSelectMethod }) {
    const [selectedId, setSelectedId] = useState(null)
    const { title, amount, currency, order_id, methods } = data

    const handleSelect = (method) => {
        setSelectedId(method.action || method.id)
        if (onSelectMethod) {
            onSelectMethod(method.action || method.label)
        }
    }

    // Icon mapping
    const getIcon = (type) => {
        switch (type) {
            case 'card': return CreditCard
            case 'upi': return Smartphone
            case 'wallet': return Wallet
            case 'qr': return QrCode
            default: return CreditCard
        }
    }

    return (
        <div className="w-full max-w-sm bg-chat-secondary rounded-2xl overflow-hidden shadow-lg border border-chat-border my-2 animate-fade-in-up">
            {/* Header */}
            <div className="bg-chat-tertiary px-5 py-4 border-b border-chat-border">
                <div className="flex justify-between items-start">
                    <div>
                        <h3 className="font-semibold text-white/90 text-lg">{title || 'Select Payment Method'}</h3>
                        <p className="text-sm text-gray-400 mt-1">Total to pay</p>
                    </div>
                    <div className="text-right">
                        <span className="text-2xl font-bold text-white tracking-tight">
                            {currency || '₹'}{amount}
                        </span>
                    </div>
                </div>
            </div>

            {/* Methods List */}
            <div className="divide-y divide-chat-border/50">
                {methods.map((method, index) => {
                    const Icon = getIcon(method.type)
                    const isSelected = selectedId === (method.action || method.id)

                    return (
                        <button
                            key={method.action || method.id || index}
                            onClick={() => handleSelect(method)}
                            className={`w-full px-5 py-4 flex items-center justify-between group transition-all duration-200 
                ${isSelected ? 'bg-accent/10' : 'hover:bg-chat-tertiary/50'}
              `}
                        >
                            <div className="flex items-center gap-4 flex-1">
                                {/* Icon Box */}
                                <div className={`
                  w-10 h-10 rounded-xl flex items-center justify-center transition-colors
                  ${isSelected ? 'bg-accent text-white' : 'bg-chat-tertiary text-gray-400 group-hover:text-white group-hover:bg-chat-tertiary/80'}
                `}>
                                    <Icon size={20} />
                                </div>

                                {/* Content */}
                                <div className="flex-1">
                                    <div className="flex items-center justify-between mb-1">
                                        <h4 className="font-semibold text-base text-white">
                                            {method.label}
                                        </h4>
                                        {isSelected && (
                                            <CheckCircle className="text-accent" size={20} />
                                        )}
                                    </div>
                                    <p className="text-sm text-gray-400">
                                        {method.description}
                                    </p>
                                </div>
                            </div>
                        </button>
                    )
                })}
            </div>

            {/* Footer Info */}
            <div className="border-t border-chat-border px-4 py-3 bg-chat-tertiary">
                <p className="text-xs text-gray-500 text-center">
                    {order_id && `Order: ${order_id} • `}
                    Secure payment powered by Razorpay
                </p>
            </div>
        </div>
    )
}

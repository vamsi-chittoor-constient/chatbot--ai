import React from 'react'
import { ShoppingCart, Plus, Minus, Trash2 } from 'lucide-react'

export const CartCard = ({ data, onUpdateQuantity, onRemoveItem, onCheckout }) => {
  const { items = [], total = 0, packaging_charge_per_item: PACKAGING_CHARGE_PER_ITEM = 30 } = data

  if (!items.length) return null

  const totalQuantity = items.reduce((sum, item) => sum + (item.quantity || 1), 0)
  const packagingCharges = totalQuantity * PACKAGING_CHARGE_PER_ITEM
  const grandTotal = total + packagingCharges

  return (
    <div className="w-full max-w-sm bg-chat-secondary border border-chat-border rounded-2xl overflow-hidden shadow-lg my-2 animate-fade-in-up">
      {/* Header */}
      <div className="bg-chat-tertiary px-5 py-4 border-b border-chat-border">
        <div className="flex items-center gap-2">
          <ShoppingCart size={18} className="text-accent" />
          <span className="font-semibold text-white/90 text-lg">Your Cart</span>
          <span className="ml-auto text-sm text-gray-400">{items.length} item{items.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Items */}
      <div className="divide-y divide-chat-border/50">
        {items.map((item, index) => (
          <div key={item.item_id || item.name || index} className="px-5 py-3 flex items-center gap-3">
            {/* Item info */}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-white truncate">{item.name}</div>
              <div className="text-xs text-gray-400">Rs.{Number(item.price).toFixed(0)} each</div>
            </div>

            {/* Quantity controls */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => {
                  if (item.quantity <= 1) {
                    onRemoveItem && onRemoveItem(item.name)
                  } else {
                    onUpdateQuantity && onUpdateQuantity(item.name, item.quantity - 1)
                  }
                }}
                className="w-7 h-7 rounded-lg bg-chat-tertiary hover:bg-red-500/20 text-gray-400 hover:text-red-400 flex items-center justify-center transition-colors"
              >
                {item.quantity <= 1 ? <Trash2 size={13} /> : <Minus size={13} />}
              </button>

              <span className="w-7 text-center text-sm font-semibold text-white">
                {item.quantity}
              </span>

              <button
                onClick={() => onUpdateQuantity && onUpdateQuantity(item.name, item.quantity + 1)}
                className="w-7 h-7 rounded-lg bg-chat-tertiary hover:bg-green-500/20 text-gray-400 hover:text-green-400 flex items-center justify-center transition-colors"
              >
                <Plus size={13} />
              </button>
            </div>

            {/* Line total */}
            <div className="text-sm font-medium text-white w-16 text-right">
              Rs.{(item.price * item.quantity).toFixed(0)}
            </div>

            {/* Delete button */}
            <button
              onClick={() => onRemoveItem && onRemoveItem(item.name)}
              className="w-7 h-7 rounded-lg hover:bg-red-500/20 text-gray-500 hover:text-red-400 flex items-center justify-center transition-colors"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>

      {/* Totals */}
      <div className="border-t border-chat-border px-5 py-3 space-y-1.5 bg-chat-tertiary/50">
        <div className="flex justify-between text-sm text-gray-400">
          <span>Subtotal</span>
          <span>Rs.{total.toFixed(0)}</span>
        </div>
        <div className="flex justify-between text-sm text-gray-400">
          <span>Packaging ({totalQuantity} x Rs.{PACKAGING_CHARGE_PER_ITEM})</span>
          <span>Rs.{packagingCharges}</span>
        </div>
        <div className="flex justify-between font-semibold text-base pt-1 border-t border-chat-border/50">
          <span className="text-white">Total</span>
          <span className="text-accent">Rs.{grandTotal.toFixed(0)}</span>
        </div>
      </div>

      {/* Checkout button */}
      {onCheckout && (
        <div className="px-5 pb-4 pt-2">
          <button
            onClick={onCheckout}
            className="w-full py-2.5 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
          >
            <ShoppingCart size={18} />
            Checkout - Rs.{grandTotal.toFixed(0)}
          </button>
        </div>
      )}
    </div>
  )
}

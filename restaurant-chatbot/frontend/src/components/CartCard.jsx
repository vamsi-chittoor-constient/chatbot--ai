import React from 'react'
import { ShoppingCart } from 'lucide-react'

const PACKAGING_CHARGE_PER_ITEM = 30

export const CartCard = ({ data }) => {
  const { items = [], total = 0 } = data

  if (!items.length) return null

  const totalQuantity = items.reduce((sum, item) => sum + (item.quantity || 1), 0)
  const packagingCharges = totalQuantity * PACKAGING_CHARGE_PER_ITEM
  const grandTotal = total + packagingCharges

  return (
    <div className="bg-chat-secondary border border-chat-border rounded-xl p-4 animate-fadeIn">
      <div className="flex items-center gap-2 font-semibold text-[15px] mb-3">
        <ShoppingCart size={18} className="text-accent" />
        <span>Your Cart</span>
      </div>

      <div className="space-y-2">
        {items.map((item, index) => (
          <div key={index} className="flex justify-between py-2 border-b border-chat-border last:border-b-0">
            <span className="text-gray-300">
              {item.name} <span className="text-gray-500">x{item.quantity}</span>
            </span>
            <span className="text-gray-300">Rs.{(item.price * item.quantity).toFixed(0)}</span>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t-2 border-chat-border space-y-1">
        <div className="flex justify-between text-sm text-gray-400">
          <span>Subtotal</span>
          <span>Rs.{total.toFixed(0)}</span>
        </div>
        <div className="flex justify-between text-sm text-gray-400">
          <span>Packaging ({totalQuantity} items x Rs.{PACKAGING_CHARGE_PER_ITEM})</span>
          <span>Rs.{packagingCharges}</span>
        </div>
        <div className="flex justify-between font-semibold text-base pt-1">
          <span>Total</span>
          <span className="text-accent">Rs.{grandTotal.toFixed(0)}</span>
        </div>
      </div>
    </div>
  )
}

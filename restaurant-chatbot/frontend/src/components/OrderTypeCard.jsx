import React from 'react'
import { UtensilsCrossed, ShoppingBag } from 'lucide-react'

export function OrderTypeCard({ data, onSubmit }) {
  const { order_id, subtotal, item_count, items_summary } = data

  const handleSelect = (orderType) => {
    onSubmit({
      form_type: 'order_type_selection',
      order_type: orderType,
      order_id,
    })
  }

  return (
    <div className="w-full max-w-sm bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl shadow-lg overflow-hidden my-3 animate-fade-in-up">
      {/* Header */}
      <div className="px-5 py-4">
        <h3 className="font-semibold text-white text-lg mb-1">How would you like your order?</h3>
        <p className="text-sm text-gray-400">
          {item_count} item{item_count !== 1 ? 's' : ''} - Rs.{subtotal?.toFixed(0)}
        </p>
        {items_summary && (
          <p className="text-xs text-gray-500 mt-1 truncate">{items_summary}</p>
        )}
      </div>

      {/* Options */}
      <div className="px-5 pb-5 space-y-3">
        <button
          onClick={() => handleSelect('dine_in')}
          className="w-full flex items-center gap-3 bg-amber-600 hover:bg-amber-700 text-white font-semibold py-3.5 px-5 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
        >
          <UtensilsCrossed size={20} />
          <div className="text-left">
            <div>Dine In</div>
            <div className="text-xs font-normal opacity-80">Reserve a table and enjoy here</div>
          </div>
        </button>

        <button
          onClick={() => handleSelect('take_away')}
          className="w-full flex items-center gap-3 bg-red-600 hover:bg-red-700 text-white font-semibold py-3.5 px-5 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
        >
          <ShoppingBag size={20} />
          <div className="text-left">
            <div>Takeaway</div>
            <div className="text-xs font-normal opacity-80">Pack it up, I'll take it to go</div>
          </div>
        </button>
      </div>
    </div>
  )
}

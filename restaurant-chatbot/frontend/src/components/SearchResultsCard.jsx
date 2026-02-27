import React, { useState } from 'react'
import { Plus, Minus, Search, Clock, CheckCircle, AlertCircle } from 'lucide-react'

/**
 * SearchResultsCard - Shows search results with per-item availability
 *
 * Used when user searches for specific items (e.g., "do u have parota")
 * Shows all matching items with clear availability indicators.
 */
export const SearchResultsCard = ({ data, onAddToCart }) => {
  const {
    query = '',
    items = [],
    currentMealPeriod = '',
    availableCount = 0,
    unavailableCount = 0
  } = data

  const [selectedItems, setSelectedItems] = useState({})

  const updateQuantity = (itemName, delta) => {
    setSelectedItems(prev => {
      const current = prev[itemName] || 0
      const newQty = Math.max(0, current + delta)
      if (newQty === 0) {
        const { [itemName]: _, ...rest } = prev
        return rest
      }
      return { ...prev, [itemName]: newQty }
    })
  }

  const handleAddToCart = () => {
    const itemsToAdd = Object.entries(selectedItems)
      .filter(([_, qty]) => qty > 0)
      .map(([name, quantity]) => {
        const item = items.find(i => i.name === name)
        return { name, quantity, price: item?.price || 0 }
      })

    if (itemsToAdd.length > 0 && onAddToCart) {
      onAddToCart(itemsToAdd)
      setSelectedItems({})
    }
  }

  // Separate available and unavailable items
  const availableItems = items.filter(item => item.is_available_now)
  const unavailableItems = items.filter(item => !item.is_available_now)

  const totalItems = Object.values(selectedItems).reduce((sum, qty) => sum + qty, 0)
  const totalPrice = Object.entries(selectedItems).reduce((sum, [name, qty]) => {
    const item = items.find(i => i.name === name)
    return sum + (item?.price || 0) * qty
  }, 0)

  if (!items.length) return null

  return (
    <div className="bg-chat-secondary rounded-xl border border-chat-border overflow-hidden animate-fadeIn">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-3">
        <h3 className="text-white font-semibold text-lg flex items-center gap-2">
          <Search size={20} />
          Search Results for "{query}"
        </h3>
        <p className="text-blue-100 text-sm">
          {items.length} item{items.length !== 1 ? 's' : ''} found
          {availableCount > 0 && ` • ${availableCount} available now`}
        </p>
      </div>

      {/* Items List */}
      <div className="max-h-80 overflow-y-auto">
        {/* Available Items Section */}
        {availableItems.length > 0 && (
          <div className="border-b border-chat-border">
            <div className="px-4 py-2 bg-green-900/20 border-b border-green-800/30">
              <span className="text-green-400 text-sm font-medium flex items-center gap-1">
                <CheckCircle size={14} />
                Available Now ({availableItems.length})
              </span>
            </div>
            <div className="px-3 py-2 space-y-2">
              {availableItems.map((item, index) => (
                <ItemRow
                  key={item.id || `avail-${index}`}
                  item={item}
                  quantity={selectedItems[item.name] || 0}
                  onUpdateQuantity={updateQuantity}
                  isAvailable={true}
                />
              ))}
            </div>
          </div>
        )}

        {/* Unavailable Items Section */}
        {unavailableItems.length > 0 && (
          <div>
            <div className="px-4 py-2 bg-orange-900/20 border-b border-orange-800/30">
              <span className="text-orange-400 text-sm font-medium flex items-center gap-1">
                <Clock size={14} />
                Available at Other Times ({unavailableItems.length})
              </span>
            </div>
            <div className="px-3 py-2 space-y-2">
              {unavailableItems.map((item, index) => (
                <ItemRow
                  key={item.id || `unavail-${index}`}
                  item={item}
                  quantity={selectedItems[item.name] || 0}
                  onUpdateQuantity={updateQuantity}
                  isAvailable={false}
                  currentMealPeriod={currentMealPeriod}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer with Total and Add to Cart */}
      <div className="border-t border-chat-border p-4 bg-chat-tertiary">
        {totalItems > 0 ? (
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">
                {totalItems} item{totalItems > 1 ? 's' : ''} selected
              </span>
              <span className="font-bold text-lg text-white">Rs.{totalPrice}</span>
            </div>
            <button
              onClick={handleAddToCart}
              className="w-full py-2.5 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
            >
              <Plus size={18} />
              Add to Cart
            </button>
          </div>
        ) : (
          <p className="text-center text-gray-500 text-sm">
            {availableItems.length > 0
              ? "Select items to add to your cart"
              : `These items aren't available right now. Check the badges above for when they're served!`
            }
          </p>
        )}
      </div>
    </div>
  )
}

/**
 * Individual item row component
 */
const ItemRow = ({ item, quantity, onUpdateQuantity, isAvailable, currentMealPeriod }) => {
  // Format meal types for display
  const formatMealTypes = (mealTypes) => {
    if (!mealTypes || mealTypes.length === 0) return 'All Day'
    if (Array.isArray(mealTypes)) {
      return mealTypes.filter(m => m !== 'All Day').join(', ') || 'All Day'
    }
    return mealTypes
  }

  return (
    <div
      className={`flex items-center justify-between p-3 rounded-lg transition-all ${
        quantity > 0
          ? 'bg-green-900/30 border border-green-700/50'
          : isAvailable
            ? 'bg-chat-bg hover:bg-gray-700/50'
            : 'bg-gray-800/30 opacity-75'
      }`}
    >
      <div className="flex-1 min-w-0 mr-3">
        <div className="flex items-center gap-2">
          <p className={`font-medium text-sm truncate ${isAvailable ? 'text-gray-200' : 'text-gray-400'}`}>
            {item.name}
          </p>
          {!isAvailable && (
            <span className="text-xs px-2 py-0.5 bg-orange-900/50 text-orange-300 rounded-full whitespace-nowrap">
              {formatMealTypes(item.meal_types)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <p className={`text-sm font-semibold ${isAvailable ? 'text-accent' : 'text-gray-500'}`}>
            Rs.{item.price}
          </p>
          {item.category && (
            <span className="text-xs text-gray-500">• {item.category}</span>
          )}
        </div>
      </div>

      {/* Quantity Controls - Only for available items */}
      {isAvailable ? (
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={() => onUpdateQuantity(item.name, -1)}
            className={`w-7 h-7 rounded-full flex items-center justify-center transition-colors ${
              quantity > 0
                ? 'bg-red-900/50 text-red-400 hover:bg-red-800/50'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }`}
            disabled={quantity === 0}
          >
            <Minus size={14} />
          </button>

          <span className="w-8 text-center text-sm font-medium text-gray-200">
            {quantity}
          </span>

          <button
            onClick={() => onUpdateQuantity(item.name, 1)}
            className="w-7 h-7 rounded-full bg-green-900/50 text-green-400 hover:bg-green-800/50 flex items-center justify-center transition-colors"
          >
            <Plus size={14} />
          </button>
        </div>
      ) : (
        <div className="flex-shrink-0">
          <span className="text-xs text-gray-500 italic">
            Not now
          </span>
        </div>
      )}
    </div>
  )
}

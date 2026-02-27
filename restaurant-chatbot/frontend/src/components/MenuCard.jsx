import React, { useState, useMemo } from 'react'
import { Plus, Minus, ShoppingCart, ChevronDown, ChevronUp, Clock, Sun, Moon, Coffee } from 'lucide-react'

// Category icons and colors
const categoryStyles = {
  'Breakfast': { emoji: '🍳', color: 'bg-yellow-900/30 border-yellow-700/50' },
  'Starters': { emoji: '🥟', color: 'bg-amber-900/30 border-amber-700/50' },
  'Main Course': { emoji: '🍛', color: 'bg-orange-900/30 border-orange-700/50' },
  'Burgers': { emoji: '🍔', color: 'bg-orange-900/30 border-orange-700/50' },
  'Pizza': { emoji: '🍕', color: 'bg-red-900/30 border-red-700/50' },
  'Pasta': { emoji: '🍝', color: 'bg-yellow-900/30 border-yellow-700/50' },
  'Salads': { emoji: '🥗', color: 'bg-green-900/30 border-green-700/50' },
  'Beverages': { emoji: '🥤', color: 'bg-blue-900/30 border-blue-700/50' },
  'Drinks': { emoji: '🥤', color: 'bg-blue-900/30 border-blue-700/50' },
  'Desserts': { emoji: '🍰', color: 'bg-pink-900/30 border-pink-700/50' },
  'Appetizers': { emoji: '🍟', color: 'bg-amber-900/30 border-amber-700/50' },
  'Snacks': { emoji: '🍿', color: 'bg-amber-900/30 border-amber-700/50' },
  'default': { emoji: '🍽️', color: 'bg-gray-800/30 border-gray-700/50' },
}

// Meal period tabs
const mealPeriodTabs = [
  { id: 'all', label: 'All', icon: Clock, color: 'bg-gray-700' },
  { id: 'Breakfast', label: 'Breakfast', icon: Coffee, color: 'bg-yellow-900/50' },
  { id: 'Lunch', label: 'Lunch', icon: Sun, color: 'bg-orange-900/50' },
  { id: 'Dinner', label: 'Dinner', icon: Moon, color: 'bg-indigo-900/50' },
]

const ITEMS_PER_PAGE = 15

// Determine meal period based on current time
const getMealPeriodByTime = () => {
  const hour = new Date().getHours()
  if (hour >= 6 && hour < 11) return 'Breakfast'
  if (hour >= 11 && hour < 16) return 'Lunch'
  if (hour >= 16 && hour < 22) return 'Dinner'
  return 'all' // Late night - show all
}

export const MenuCard = ({ data, onAddToCart }) => {
  const { items = [], currentMealPeriod, showMealFilters = true } = data
  const [selectedItems, setSelectedItems] = useState({})
  const [expandedCategories, setExpandedCategories] = useState(new Set())
  // Auto-detect meal period based on time if not provided (only if meal filters are shown)
  const [activeMealTab, setActiveMealTab] = useState(showMealFilters ? (currentMealPeriod || getMealPeriodByTime()) : 'all')
  const [visibleCount, setVisibleCount] = useState(ITEMS_PER_PAGE)

  // Filter items by meal period
  const filteredItems = useMemo(() => {
    if (activeMealTab === 'all') {
      // "All" tab shows only items available RIGHT NOW based on time of day.
      // This prevents users from seeing (and trying to order) items the backend
      // will reject because they're outside their meal-time window.
      const currentPeriod = getMealPeriodByTime()
      if (currentPeriod === 'all') {
        // Late night (22:00–06:00): only "All Day" tagged items are orderable
        return items.filter(item => {
          const mealTypes = item.meal_types || ['All Day']
          return mealTypes.includes('All Day')
        })
      }
      // During a specific meal period: show items for that period + All Day
      return items.filter(item => {
        const mealTypes = item.meal_types || ['All Day']
        return mealTypes.includes(currentPeriod) || mealTypes.includes('All Day')
      })
    }
    return items.filter(item => {
      const mealTypes = item.meal_types || ['All Day']
      return mealTypes.includes(activeMealTab) || mealTypes.includes('All Day')
    })
  }, [items, activeMealTab])

  // Get visible items (for pagination)
  const visibleItems = useMemo(() => {
    return filteredItems.slice(0, visibleCount)
  }, [filteredItems, visibleCount])

  // Group visible items by category
  const categorizedItems = useMemo(() => {
    const grouped = visibleItems.reduce((acc, item) => {
      const category = item.category || 'Other'
      if (!acc[category]) {
        acc[category] = []
      }
      acc[category].push(item)
      return acc
    }, {})

    // Auto-expand first few categories
    if (expandedCategories.size === 0) {
      const keys = Object.keys(grouped).slice(0, 3)
      setExpandedCategories(new Set(keys))
    }

    return grouped
  }, [visibleItems])

  const toggleCategory = (category) => {
    setExpandedCategories(prev => {
      const newExpanded = new Set(prev)
      if (newExpanded.has(category)) {
        newExpanded.delete(category)
      } else {
        newExpanded.add(category)
      }
      return newExpanded
    })
  }

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

  const handleConfirm = () => {
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

  const handleLoadMore = () => {
    setVisibleCount(prev => prev + ITEMS_PER_PAGE)
  }

  const totalItems = Object.values(selectedItems).reduce((sum, qty) => sum + qty, 0)
  const totalPrice = Object.entries(selectedItems).reduce((sum, [name, qty]) => {
    const item = items.find(i => i.name === name)
    return sum + (item?.price || 0) * qty
  }, 0)

  const getCategoryStyle = (category) => {
    return categoryStyles[category] || categoryStyles['default']
  }

  const hasMore = visibleCount < filteredItems.length

  if (!items.length) return null

  return (
    <div className="bg-chat-secondary rounded-xl border border-chat-border overflow-hidden animate-fadeIn">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-red-600 px-4 py-3">
        <h3 className="text-white font-semibold text-lg flex items-center gap-2">
          🍽️ Our Menu
        </h3>
        <p className="text-orange-100 text-sm">
          {filteredItems.length} items available
        </p>
      </div>

      {/* Meal Period Tabs - Only show if showMealFilters is true */}
      {showMealFilters && (
        <div className="flex border-b border-chat-border bg-chat-tertiary px-2 py-1.5 gap-1 overflow-x-auto">
          {mealPeriodTabs.map(tab => {
            const Icon = tab.icon
            const isActive = activeMealTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveMealTab(tab.id)
                  setVisibleCount(ITEMS_PER_PAGE)
                }}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? `${tab.color} text-white shadow-sm`
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
                }`}
              >
                <Icon size={14} />
                {tab.label}
              </button>
            )
          })}
        </div>
      )}

      {/* Categories */}
      <div className="max-h-80 overflow-y-auto">
        {Object.entries(categorizedItems).map(([category, categoryItems]) => {
          const style = getCategoryStyle(category)
          const isExpanded = expandedCategories.has(category)

          return (
            <div key={category} className="border-b border-chat-border last:border-b-0">
              {/* Category Header */}
              <button
                onClick={() => toggleCategory(category)}
                className={`w-full px-4 py-2 flex items-center justify-between ${style.color} hover:opacity-80 transition-all`}
              >
                <span className="font-medium text-gray-200 flex items-center gap-2">
                  <span>{style.emoji}</span>
                  {category}
                  <span className="text-xs text-gray-400">({categoryItems.length})</span>
                </span>
                {isExpanded ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
              </button>

              {/* Items */}
              {isExpanded && (
                <div className="px-3 py-2 space-y-2">
                  {categoryItems.map((item, index) => {
                    const qty = selectedItems[item.name] || 0
                    // Use id if available, otherwise use category + index for unique key
                    const itemKey = item.id || item.menu_item_id || `${category}-${index}`
                    return (
                      <div
                        key={itemKey}
                        className={`flex items-center justify-between p-2 rounded-lg transition-all ${
                          qty > 0 ? 'bg-green-900/30 border border-green-700/50' : 'bg-chat-bg hover:bg-gray-700/50'
                        }`}
                      >
                        <div className="flex-1 min-w-0 mr-2">
                          <p className="font-medium text-gray-200 text-sm truncate">{item.name}</p>
                          <p className="text-accent text-sm font-semibold">Rs.{item.price}</p>
                        </div>

                        {/* Quantity Controls */}
                        <div className="flex items-center gap-1 flex-shrink-0">
                          <button
                            onClick={() => updateQuantity(item.name, -1)}
                            className={`w-7 h-7 rounded-full flex items-center justify-center transition-colors ${
                              qty > 0
                                ? 'bg-red-900/50 text-red-400 hover:bg-red-800/50'
                                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                            }`}
                            disabled={qty === 0}
                          >
                            <Minus size={14} />
                          </button>

                          <span className="w-8 text-center text-sm font-medium text-gray-200">
                            {qty}
                          </span>

                          <button
                            onClick={() => updateQuantity(item.name, 1)}
                            className="w-7 h-7 rounded-full bg-green-900/50 text-green-400 hover:bg-green-800/50 flex items-center justify-center transition-colors"
                          >
                            <Plus size={14} />
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}

        {/* Load More Button */}
        {hasMore && (
          <div className="px-4 py-3 bg-chat-tertiary border-t border-chat-border">
            <button
              onClick={handleLoadMore}
              className="w-full py-2 text-accent font-medium text-sm hover:text-accent-hover hover:bg-gray-700/30 rounded-lg transition-colors"
            >
              Load More ({filteredItems.length - visibleCount} more items)
            </button>
          </div>
        )}
      </div>

      {/* Footer with Total and Confirm */}
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
              onClick={handleConfirm}
              className="w-full py-2.5 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
            >
              <ShoppingCart size={18} />
              Add to Cart
            </button>
          </div>
        ) : (
          <p className="text-center text-gray-500 text-sm">
            Select items to add to your cart
          </p>
        )}
      </div>
    </div>
  )
}

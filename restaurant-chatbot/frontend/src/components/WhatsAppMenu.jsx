import React, { useState, useEffect, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { Plus, Minus, ShoppingCart, ChevronDown, ChevronUp, Loader2, CheckCircle, AlertCircle } from 'lucide-react'

const categoryStyles = {
  'Breakfast': { emoji: '🍳', color: 'from-yellow-600 to-yellow-700' },
  'Starters': { emoji: '🥟', color: 'from-amber-600 to-amber-700' },
  'Main Course': { emoji: '🍛', color: 'from-orange-600 to-orange-700' },
  'Burgers': { emoji: '🍔', color: 'from-orange-600 to-orange-700' },
  'Pizza': { emoji: '🍕', color: 'from-red-600 to-red-700' },
  'Pasta': { emoji: '🍝', color: 'from-yellow-600 to-yellow-700' },
  'Salads': { emoji: '🥗', color: 'from-green-600 to-green-700' },
  'Beverages': { emoji: '🥤', color: 'from-blue-600 to-blue-700' },
  'Drinks': { emoji: '🥤', color: 'from-blue-600 to-blue-700' },
  'Desserts': { emoji: '🍰', color: 'from-pink-600 to-pink-700' },
  'Appetizers': { emoji: '🍟', color: 'from-amber-600 to-amber-700' },
  'Snacks': { emoji: '🍿', color: 'from-amber-600 to-amber-700' },
  'default': { emoji: '🍽️', color: 'from-gray-600 to-gray-700' },
}

const getCategoryStyle = (cat) => categoryStyles[cat] || categoryStyles['default']

export default function WhatsAppMenu() {
  const { sessionId } = useParams()
  const [items, setItems] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedItems, setSelectedItems] = useState({})
  const [expandedCategories, setExpandedCategories] = useState(new Set())
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  // Fetch menu data
  useEffect(() => {
    const fetchMenu = async () => {
      try {
        const resp = await fetch(`/api/v1/menu/whatsapp/${sessionId}`)
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}))
          throw new Error(data.detail || 'Failed to load menu')
        }
        const data = await resp.json()
        setItems(data.items || [])
        setCategories(data.categories || [])
        // Auto-expand first 3 categories
        setExpandedCategories(new Set((data.categories || []).slice(0, 3)))
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchMenu()
  }, [sessionId])

  // Group items by category
  const categorizedItems = useMemo(() => {
    const grouped = {}
    for (const item of items) {
      const cat = item.category || 'Other'
      if (!grouped[cat]) grouped[cat] = []
      grouped[cat].push(item)
    }
    return grouped
  }, [items])

  const toggleCategory = (cat) => {
    setExpandedCategories(prev => {
      const next = new Set(prev)
      if (next.has(cat)) next.delete(cat)
      else next.add(cat)
      return next
    })
  }

  const updateQty = (itemName, delta) => {
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

  const totalItems = Object.values(selectedItems).reduce((s, q) => s + q, 0)
  const totalPrice = Object.entries(selectedItems).reduce((s, [name, qty]) => {
    const item = items.find(i => i.name === name)
    return s + (item?.price || 0) * qty
  }, 0)

  const handleSubmit = async () => {
    const cartItems = Object.entries(selectedItems)
      .filter(([_, qty]) => qty > 0)
      .map(([name, quantity]) => {
        const item = items.find(i => i.name === name)
        return { name, quantity, price: item?.price || 0 }
      })

    if (!cartItems.length) return

    setSubmitting(true)
    try {
      const resp = await fetch('/api/v1/cart/whatsapp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: sessionId, items: cartItems }),
      })
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to add to cart')
      }
      setSubmitted(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 size={40} className="animate-spin text-orange-500 mx-auto mb-4" />
          <p className="text-gray-400">Loading menu...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error && !items.length) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
        <div className="text-center max-w-sm">
          <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
          <h2 className="text-white text-lg font-semibold mb-2">Oops!</h2>
          <p className="text-gray-400 mb-4">{error}</p>
          <p className="text-gray-500 text-sm">Please go back to WhatsApp and request the menu again.</p>
        </div>
      </div>
    )
  }

  // Success state
  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
        <div className="text-center max-w-sm">
          <CheckCircle size={56} className="text-green-500 mx-auto mb-4" />
          <h2 className="text-white text-xl font-semibold mb-2">Added to Cart!</h2>
          <p className="text-gray-400 mb-2">
            {totalItems} item{totalItems > 1 ? 's' : ''} • ₹{totalPrice}
          </p>
          <p className="text-gray-500 text-sm mb-6">
            You can close this page and return to WhatsApp to continue your order.
          </p>
          <button
            onClick={() => { setSubmitted(false); setSelectedItems({}) }}
            className="px-6 py-2 bg-orange-600 text-white rounded-lg font-medium hover:bg-orange-700 transition"
          >
            Add More Items
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-600 to-red-600 px-4 py-4 sticky top-0 z-10 shadow-lg">
        <h1 className="text-white font-bold text-xl">🍽️ A24 Menu</h1>
        <p className="text-orange-100 text-sm">{items.length} items available</p>
      </header>

      {/* Error banner */}
      {error && (
        <div className="bg-red-900/50 border-b border-red-700 px-4 py-2 text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Menu items */}
      <main className="flex-1 overflow-y-auto pb-28">
        {categories.map(cat => {
          const catItems = categorizedItems[cat] || []
          if (!catItems.length) return null
          const style = getCategoryStyle(cat)
          const isExpanded = expandedCategories.has(cat)

          return (
            <div key={cat} className="border-b border-gray-800">
              {/* Category header */}
              <button
                onClick={() => toggleCategory(cat)}
                className={`w-full px-4 py-3 flex items-center justify-between bg-gradient-to-r ${style.color} active:opacity-80`}
              >
                <span className="font-semibold text-white flex items-center gap-2">
                  <span className="text-lg">{style.emoji}</span>
                  {cat}
                  <span className="text-xs text-white/70 font-normal">({catItems.length})</span>
                </span>
                {isExpanded
                  ? <ChevronUp size={18} className="text-white/70" />
                  : <ChevronDown size={18} className="text-white/70" />
                }
              </button>

              {/* Items */}
              {isExpanded && (
                <div className="px-3 py-2 space-y-1.5">
                  {catItems.map((item, idx) => {
                    const qty = selectedItems[item.name] || 0
                    return (
                      <div
                        key={item.id || item.menu_item_id || `${cat}-${idx}`}
                        className={`flex items-center justify-between p-3 rounded-xl transition-all ${
                          qty > 0
                            ? 'bg-green-900/30 border border-green-700/50'
                            : 'bg-gray-900/50 border border-gray-800 active:bg-gray-800'
                        }`}
                      >
                        <div className="flex-1 min-w-0 mr-3">
                          <p className="font-medium text-gray-100 text-[15px]">{item.name}</p>
                          <p className="text-orange-400 text-sm font-semibold">₹{item.price}</p>
                        </div>

                        {/* Qty controls */}
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {qty > 0 && (
                            <button
                              onClick={() => updateQty(item.name, -1)}
                              className="w-9 h-9 rounded-full bg-red-900/60 text-red-300 flex items-center justify-center active:bg-red-800"
                            >
                              <Minus size={16} />
                            </button>
                          )}
                          {qty > 0 && (
                            <span className="w-8 text-center text-sm font-bold text-white">{qty}</span>
                          )}
                          <button
                            onClick={() => updateQty(item.name, 1)}
                            className="w-9 h-9 rounded-full bg-green-900/60 text-green-300 flex items-center justify-center active:bg-green-800"
                          >
                            <Plus size={16} />
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
      </main>

      {/* Sticky bottom bar */}
      {totalItems > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 p-4 shadow-2xl z-20">
          <div className="flex items-center justify-between mb-3">
            <span className="text-gray-400 text-sm">
              {totalItems} item{totalItems > 1 ? 's' : ''} selected
            </span>
            <span className="text-white font-bold text-lg">₹{totalPrice}</span>
          </div>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full py-3.5 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 active:bg-green-800 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {submitting ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <ShoppingCart size={20} />
            )}
            {submitting ? 'Adding...' : 'Add to Cart'}
          </button>
        </div>
      )}
    </div>
  )
}

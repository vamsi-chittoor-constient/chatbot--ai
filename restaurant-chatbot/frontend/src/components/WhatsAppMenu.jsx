import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Plus, Minus, ShoppingCart, ChevronDown, ChevronUp, Loader2, CheckCircle, AlertCircle, Trash2, Search, Package, Clock } from 'lucide-react'

// ── Shared styles ──
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
const getCatStyle = (c) => categoryStyles[c] || categoryStyles['default']

// ── Shared components ──
const PageShell = ({ children }) => (
  <div className="min-h-screen bg-gray-950 flex flex-col text-gray-100">{children}</div>
)

const LoadingScreen = () => (
  <PageShell>
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <Loader2 size={40} className="animate-spin text-orange-500 mx-auto mb-4" />
        <p className="text-gray-400">Loading...</p>
      </div>
    </div>
  </PageShell>
)

const ErrorScreen = ({ message }) => (
  <PageShell>
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="text-center max-w-sm">
        <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
        <h2 className="text-white text-lg font-semibold mb-2">Oops!</h2>
        <p className="text-gray-400 mb-4">{message}</p>
        <p className="text-gray-500 text-sm">Go back to WhatsApp and try again.</p>
      </div>
    </div>
  </PageShell>
)

const SuccessScreen = ({ title, subtitle, onAction, actionLabel }) => (
  <PageShell>
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="text-center max-w-sm">
        <CheckCircle size={56} className="text-green-500 mx-auto mb-4" />
        <h2 className="text-white text-xl font-semibold mb-2">{title}</h2>
        <p className="text-gray-400 mb-2">{subtitle}</p>
        <p className="text-gray-500 text-sm mb-6">You can close this page and return to WhatsApp.</p>
        {onAction && (
          <button onClick={onAction} className="px-6 py-2 bg-orange-600 text-white rounded-lg font-medium active:bg-orange-700">
            {actionLabel || 'Continue'}
          </button>
        )}
      </div>
    </div>
  </PageShell>
)

const QtyControls = ({ qty, onMinus, onPlus, showZero = false }) => (
  <div className="flex items-center gap-2 flex-shrink-0">
    {(qty > 0 || showZero) && (
      <button onClick={onMinus} className="w-9 h-9 rounded-full bg-red-900/60 text-red-300 flex items-center justify-center active:bg-red-800">
        <Minus size={16} />
      </button>
    )}
    {(qty > 0 || showZero) && (
      <span className="w-8 text-center text-sm font-bold text-white">{qty}</span>
    )}
    <button onClick={onPlus} className="w-9 h-9 rounded-full bg-green-900/60 text-green-300 flex items-center justify-center active:bg-green-800">
      <Plus size={16} />
    </button>
  </div>
)

// ── API helpers ──
const apiBase = '/api/v1'

async function fetchPageData(token) {
  const resp = await fetch(`${apiBase}/wa/page/${token}`)
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}))
    throw new Error(data.detail || 'Failed to load')
  }
  return resp.json()
}

async function postAction(token, action, data = {}) {
  const resp = await fetch(`${apiBase}/wa/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, action, data }),
  })
  if (!resp.ok) {
    const d = await resp.json().catch(() => ({}))
    throw new Error(d.detail || 'Action failed')
  }
  return resp.json()
}

// ══════════════════════════════════════════════════════
// MENU PAGE
// ══════════════════════════════════════════════════════
function MenuPage({ data, token }) {
  const { items = [], categories = [] } = data
  const [selected, setSelected] = useState({})
  const [expanded, setExpanded] = useState(new Set(categories.slice(0, 3)))
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const grouped = useMemo(() => {
    const g = {}
    const query = searchQuery.toLowerCase().trim()
    for (const item of items) {
      if (query && !item.name.toLowerCase().includes(query) && !(item.category || '').toLowerCase().includes(query)) continue
      const cat = item.category || 'Other'
      if (!g[cat]) g[cat] = []
      g[cat].push(item)
    }
    return g
  }, [items, searchQuery])

  const visibleCategories = useMemo(() => categories.filter(c => grouped[c]?.length), [categories, grouped])

  const toggle = (c) => setExpanded(p => { const n = new Set(p); n.has(c) ? n.delete(c) : n.add(c); return n })
  const updateQty = (name, d) => setSelected(p => {
    const q = Math.max(0, (p[name] || 0) + d)
    if (q === 0) { const { [name]: _, ...r } = p; return r }
    return { ...p, [name]: q }
  })

  const totalItems = Object.values(selected).reduce((s, q) => s + q, 0)
  const totalPrice = Object.entries(selected).reduce((s, [n, q]) => {
    const it = items.find(i => i.name === n)
    return s + (it?.price || 0) * q
  }, 0)

  const handleSubmit = async () => {
    const cart = Object.entries(selected).filter(([_, q]) => q > 0).map(([name, quantity]) => {
      const it = items.find(i => i.name === name)
      return { name, quantity, price: it?.price || 0 }
    })
    if (!cart.length) return
    setSubmitting(true)
    try {
      await postAction(token, 'add_to_cart', { items: cart })
      setDone(true)
    } catch (e) { alert(e.message) }
    finally { setSubmitting(false) }
  }

  if (done) return <SuccessScreen title="Added to Cart!" subtitle={`${totalItems} item${totalItems > 1 ? 's' : ''} - Rs.${totalPrice}`} onAction={() => { setDone(false); setSelected({}) }} actionLabel="Add More Items" />

  return (
    <PageShell>
      <header className="bg-gradient-to-r from-orange-600 to-red-600 px-4 py-4 sticky top-0 z-10 shadow-lg">
        <h1 className="text-white font-bold text-xl">🍽️ A24 Menu</h1>
        <p className="text-orange-100 text-sm">{items.length} items available</p>
      </header>

      {/* Search */}
      <div className="px-4 py-3 bg-gray-900 border-b border-gray-800 sticky top-[68px] z-10">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search items..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-orange-500"
          />
        </div>
      </div>

      <main className="flex-1 overflow-y-auto pb-28">
        {visibleCategories.map(cat => {
          const catItems = grouped[cat] || []
          const style = getCatStyle(cat)
          const isExp = expanded.has(cat)
          return (
            <div key={cat} className="border-b border-gray-800">
              <button onClick={() => toggle(cat)} className={`w-full px-4 py-3 flex items-center justify-between bg-gradient-to-r ${style.color} active:opacity-80`}>
                <span className="font-semibold text-white flex items-center gap-2">
                  <span className="text-lg">{style.emoji}</span> {cat}
                  <span className="text-xs text-white/70 font-normal">({catItems.length})</span>
                </span>
                {isExp ? <ChevronUp size={18} className="text-white/70" /> : <ChevronDown size={18} className="text-white/70" />}
              </button>
              {isExp && (
                <div className="px-3 py-2 space-y-1.5">
                  {catItems.map((item, idx) => {
                    const qty = selected[item.name] || 0
                    return (
                      <div key={item.id || `${cat}-${idx}`} className={`flex items-center justify-between p-3 rounded-xl transition-all ${qty > 0 ? 'bg-green-900/30 border border-green-700/50' : 'bg-gray-900/50 border border-gray-800'}`}>
                        <div className="flex-1 min-w-0 mr-3">
                          <p className="font-medium text-gray-100 text-[15px]">{item.name}</p>
                          <p className="text-orange-400 text-sm font-semibold">Rs.{item.price}</p>
                        </div>
                        <QtyControls qty={qty} onMinus={() => updateQty(item.name, -1)} onPlus={() => updateQty(item.name, 1)} />
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
        {visibleCategories.length === 0 && <p className="text-center text-gray-500 py-10">No items found</p>}
      </main>

      {totalItems > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 p-4 shadow-2xl z-20">
          <div className="flex items-center justify-between mb-3">
            <span className="text-gray-400 text-sm">{totalItems} item{totalItems > 1 ? 's' : ''}</span>
            <span className="text-white font-bold text-lg">Rs.{totalPrice}</span>
          </div>
          <button onClick={handleSubmit} disabled={submitting} className="w-full py-3.5 bg-green-600 text-white font-semibold rounded-xl active:bg-green-800 transition flex items-center justify-center gap-2 disabled:opacity-50">
            {submitting ? <Loader2 size={20} className="animate-spin" /> : <ShoppingCart size={20} />}
            {submitting ? 'Adding...' : 'Add to Cart'}
          </button>
        </div>
      )}
    </PageShell>
  )
}

// ══════════════════════════════════════════════════════
// CART PAGE
// ══════════════════════════════════════════════════════
function CartPage({ data, token }) {
  const [items, setItems] = useState(data.items || [])
  const packagingRate = data.packaging_charge || 30
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const [actionType, setActionType] = useState('')

  const subtotal = items.reduce((s, it) => s + (it.price || 0) * (it.quantity || 1), 0)
  const packaging = packagingRate * items.length
  const total = subtotal + packaging

  const updateQty = (name, delta) => {
    setItems(prev => prev.map(it => {
      if ((it.name || it.item_name) !== name) return it
      const newQty = Math.max(0, (it.quantity || 1) + delta)
      return { ...it, quantity: newQty }
    }).filter(it => (it.quantity || 1) > 0))
  }

  const removeItem = (name) => {
    setItems(prev => prev.filter(it => (it.name || it.item_name) !== name))
  }

  const handleAction = async (action) => {
    setSubmitting(true)
    setActionType(action)
    try {
      if (action === 'checkout') {
        await postAction(token, 'checkout')
      } else if (action === 'update') {
        const origItems = data.items || []
        const updates = []
        const removes = []
        for (const orig of origItems) {
          const n = orig.name || orig.item_name
          const current = items.find(it => (it.name || it.item_name) === n)
          if (!current) {
            removes.push(n)
          } else if (current.quantity !== orig.quantity) {
            updates.push({ item_name: n, quantity: current.quantity })
          }
        }
        if (updates.length || removes.length) {
          await postAction(token, 'update_cart', { updates, removes })
        }
      } else if (action === 'add_more') {
        await postAction(token, 'add_more')
      }
      setDone(true)
    } catch (e) { alert(e.message) }
    finally { setSubmitting(false) }
  }

  if (done) {
    const msg = actionType === 'checkout' ? 'Proceeding to checkout...' : actionType === 'add_more' ? 'Opening menu...' : 'Cart updated!'
    return <SuccessScreen title={msg} subtitle="Check WhatsApp for next steps." />
  }

  if (!items.length) {
    return (
      <PageShell>
        <header className="bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-4">
          <h1 className="text-white font-bold text-xl">🛒 Your Cart</h1>
        </header>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-500">Your cart is empty</p>
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <header className="bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-4 sticky top-0 z-10 shadow-lg">
        <h1 className="text-white font-bold text-xl">🛒 Your Cart</h1>
        <p className="text-blue-100 text-sm">{items.length} item{items.length > 1 ? 's' : ''}</p>
      </header>

      <main className="flex-1 overflow-y-auto pb-48 px-3 py-3 space-y-2">
        {items.map((item, idx) => {
          const name = item.name || item.item_name || 'Item'
          const qty = item.quantity || 1
          const price = item.price || 0
          return (
            <div key={`${name}-${idx}`} className="bg-gray-900/50 border border-gray-800 rounded-xl p-3 flex items-center gap-3">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-100 text-[15px]">{name}</p>
                <p className="text-orange-400 text-sm font-semibold">Rs.{price} x {qty} = Rs.{price * qty}</p>
              </div>
              <QtyControls qty={qty} onMinus={() => updateQty(name, -1)} onPlus={() => updateQty(name, 1)} showZero />
              <button onClick={() => removeItem(name)} className="w-8 h-8 rounded-full bg-red-900/40 text-red-400 flex items-center justify-center active:bg-red-800">
                <Trash2 size={14} />
              </button>
            </div>
          )
        })}
      </main>

      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 p-4 shadow-2xl z-20 space-y-3">
        <div className="text-sm space-y-1">
          <div className="flex justify-between text-gray-400"><span>Subtotal</span><span>Rs.{subtotal}</span></div>
          <div className="flex justify-between text-gray-400"><span>Packaging ({items.length} x Rs.{packagingRate})</span><span>Rs.{packaging}</span></div>
          <div className="flex justify-between text-white font-bold text-lg pt-1 border-t border-gray-700"><span>Total</span><span>Rs.{total}</span></div>
        </div>
        <div className="flex gap-2">
          <button onClick={() => handleAction('update')} disabled={submitting} className="flex-1 py-3 bg-gray-700 text-white font-semibold rounded-xl active:bg-gray-600 disabled:opacity-50">
            {submitting && actionType === 'update' ? <Loader2 size={18} className="animate-spin mx-auto" /> : 'Update Cart'}
          </button>
          <button onClick={() => handleAction('checkout')} disabled={submitting} className="flex-1 py-3 bg-green-600 text-white font-semibold rounded-xl active:bg-green-800 disabled:opacity-50">
            {submitting && actionType === 'checkout' ? <Loader2 size={18} className="animate-spin mx-auto" /> : 'Checkout'}
          </button>
        </div>
        <button onClick={() => handleAction('add_more')} disabled={submitting} className="w-full py-2.5 bg-orange-600/20 text-orange-400 font-medium rounded-xl active:bg-orange-600/30 disabled:opacity-50 text-sm">
          + Add More Items
        </button>
      </div>
    </PageShell>
  )
}

// ══════════════════════════════════════════════════════
// SEARCH RESULTS PAGE
// ══════════════════════════════════════════════════════
function SearchPage({ data, token }) {
  const { items = [], query = '' } = data
  const [selected, setSelected] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  const available = items.filter(i => i.is_available_now !== false)
  const unavailable = items.filter(i => i.is_available_now === false)

  const updateQty = (name, d) => setSelected(p => {
    const q = Math.max(0, (p[name] || 0) + d)
    if (q === 0) { const { [name]: _, ...r } = p; return r }
    return { ...p, [name]: q }
  })

  const totalItems = Object.values(selected).reduce((s, q) => s + q, 0)
  const totalPrice = Object.entries(selected).reduce((s, [n, q]) => {
    const it = items.find(i => i.name === n)
    return s + (it?.price || 0) * q
  }, 0)

  const handleSubmit = async () => {
    const cart = Object.entries(selected).filter(([_, q]) => q > 0).map(([name, quantity]) => {
      const it = items.find(i => i.name === name)
      return { name, quantity, price: it?.price || 0 }
    })
    if (!cart.length) return
    setSubmitting(true)
    try {
      await postAction(token, 'add_to_cart', { items: cart })
      setDone(true)
    } catch (e) { alert(e.message) }
    finally { setSubmitting(false) }
  }

  if (done) return <SuccessScreen title="Added to Cart!" subtitle={`${totalItems} item${totalItems > 1 ? 's' : ''} - Rs.${totalPrice}`} />

  return (
    <PageShell>
      <header className="bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-4 sticky top-0 z-10 shadow-lg">
        <h1 className="text-white font-bold text-xl">🔍 Search Results</h1>
        <p className="text-purple-100 text-sm">"{query}" — {items.length} items found</p>
      </header>

      <main className="flex-1 overflow-y-auto pb-28 px-3 py-3 space-y-1.5">
        {available.length > 0 && (
          <>
            <p className="text-green-400 font-semibold text-sm px-1 pt-2">✅ Available Now ({available.length})</p>
            {available.map((item, idx) => {
              const qty = selected[item.name] || 0
              return (
                <div key={item.id || idx} className={`flex items-center justify-between p-3 rounded-xl ${qty > 0 ? 'bg-green-900/30 border border-green-700/50' : 'bg-gray-900/50 border border-gray-800'}`}>
                  <div className="flex-1 min-w-0 mr-3">
                    <p className="font-medium text-gray-100 text-[15px]">{item.name}</p>
                    <p className="text-orange-400 text-sm font-semibold">Rs.{item.price}
                      {item.category && <span className="text-gray-500 font-normal"> · {item.category}</span>}
                    </p>
                  </div>
                  <QtyControls qty={qty} onMinus={() => updateQty(item.name, -1)} onPlus={() => updateQty(item.name, 1)} />
                </div>
              )
            })}
          </>
        )}
        {unavailable.length > 0 && (
          <>
            <p className="text-gray-500 font-semibold text-sm px-1 pt-4 flex items-center gap-1"><Clock size={14} /> Available Later ({unavailable.length})</p>
            {unavailable.map((item, idx) => (
              <div key={`u-${idx}`} className="flex items-center justify-between p-3 rounded-xl bg-gray-900/30 border border-gray-800 opacity-60">
                <div className="flex-1 min-w-0 mr-3">
                  <p className="font-medium text-gray-400 text-[15px]">{item.name}</p>
                  <p className="text-gray-500 text-sm">Rs.{item.price} · {(item.meal_types || []).join(', ') || 'Later'}</p>
                </div>
              </div>
            ))}
          </>
        )}
      </main>

      {totalItems > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 p-4 shadow-2xl z-20">
          <div className="flex items-center justify-between mb-3">
            <span className="text-gray-400 text-sm">{totalItems} item{totalItems > 1 ? 's' : ''}</span>
            <span className="text-white font-bold text-lg">Rs.{totalPrice}</span>
          </div>
          <button onClick={handleSubmit} disabled={submitting} className="w-full py-3.5 bg-green-600 text-white font-semibold rounded-xl active:bg-green-800 flex items-center justify-center gap-2 disabled:opacity-50">
            {submitting ? <Loader2 size={20} className="animate-spin" /> : <ShoppingCart size={20} />}
            {submitting ? 'Adding...' : 'Add to Cart'}
          </button>
        </div>
      )}
    </PageShell>
  )
}

// ══════════════════════════════════════════════════════
// ORDER PAGE
// ══════════════════════════════════════════════════════
function OrderPage({ data }) {
  const { order_id, items = [], total, status, order_type } = data
  const statusColors = {
    pending: 'text-yellow-400 bg-yellow-900/30',
    confirmed: 'text-green-400 bg-green-900/30',
    preparing: 'text-blue-400 bg-blue-900/30',
    ready: 'text-green-400 bg-green-900/30',
    delivered: 'text-gray-400 bg-gray-800',
    cancelled: 'text-red-400 bg-red-900/30',
  }
  const sc = statusColors[status?.toLowerCase()] || statusColors.pending

  return (
    <PageShell>
      <header className="bg-gradient-to-r from-teal-600 to-cyan-600 px-4 py-4">
        <h1 className="text-white font-bold text-xl">📋 Order Details</h1>
        {order_id && <p className="text-teal-100 text-sm">#{order_id}</p>}
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* Status badge */}
        <div className="flex items-center gap-3">
          {status && <span className={`px-3 py-1 rounded-full text-sm font-semibold ${sc}`}>{status.replace('_', ' ').toUpperCase()}</span>}
          {order_type && <span className="px-3 py-1 rounded-full text-sm bg-gray-800 text-gray-300">{order_type.replace('_', ' ')}</span>}
        </div>

        {/* Items */}
        <div className="space-y-2">
          {items.map((item, idx) => {
            const name = item.name || item.item_name || 'Item'
            const qty = item.quantity || 1
            const price = item.price || 0
            return (
              <div key={idx} className="flex justify-between items-center p-3 bg-gray-900/50 border border-gray-800 rounded-xl">
                <div>
                  <p className="font-medium text-gray-100">{name}</p>
                  <p className="text-gray-500 text-sm">x{qty}</p>
                </div>
                <p className="text-orange-400 font-semibold">Rs.{price * qty}</p>
              </div>
            )
          })}
        </div>

        {/* Total */}
        <div className="border-t border-gray-700 pt-3 flex justify-between items-center">
          <span className="text-gray-400 font-semibold">Total</span>
          <span className="text-white font-bold text-xl">Rs.{total}</span>
        </div>
      </main>

      <div className="p-4 bg-gray-900 border-t border-gray-700">
        <p className="text-center text-gray-500 text-sm">Close this page and return to WhatsApp for updates.</p>
      </div>
    </PageShell>
  )
}

// ══════════════════════════════════════════════════════
// MAIN ROUTER
// ══════════════════════════════════════════════════════
export default function WhatsAppMenu() {
  const { sessionId } = useParams()
  const [pageData, setPageData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchPageData(sessionId)
      .then(setPageData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [sessionId])

  if (loading) return <LoadingScreen />
  if (error) return <ErrorScreen message={error} />
  if (!pageData) return <ErrorScreen message="No data available" />

  switch (pageData.page_type) {
    case 'menu': return <MenuPage data={pageData} token={sessionId} />
    case 'cart': return <CartPage data={pageData} token={sessionId} />
    case 'search': return <SearchPage data={pageData} token={sessionId} />
    case 'order': return <OrderPage data={pageData} />
    default: return <ErrorScreen message={`Unknown page: ${pageData.page_type}`} />
  }
}

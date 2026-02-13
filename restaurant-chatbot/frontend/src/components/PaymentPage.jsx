import React, { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { CreditCard, Wallet, Smartphone, Loader2, AlertCircle, CheckCircle, ArrowLeft, ShoppingBag } from 'lucide-react'

function PaymentPage() {
  const { orderId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const sessionId = searchParams.get('sid')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [orderData, setOrderData] = useState(null)
  const [selecting, setSelecting] = useState(false)
  const [result, setResult] = useState(null) // { step, payment_link }

  // Fetch order summary on mount
  useEffect(() => {
    if (!sessionId) {
      setError('Missing session ID')
      setLoading(false)
      return
    }

    fetch(`/api/v1/payment/order-summary?session_id=${encodeURIComponent(sessionId)}`)
      .then(res => {
        if (!res.ok) throw new Error(res.status === 404 ? 'No pending payment found' : 'Failed to load order')
        return res.json()
      })
      .then(data => {
        setOrderData(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [sessionId])

  const handleSelectMethod = async (method) => {
    setSelecting(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/payment/select-method', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, method })
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || 'Payment failed')
      }
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
      setSelecting(false)
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-chat-bg">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-accent animate-spin" />
          <p className="text-gray-400 text-lg">Loading order...</p>
        </div>
      </div>
    )
  }

  // Error state (no order)
  if (error && !orderData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-chat-bg px-4">
        <div className="bg-chat-secondary rounded-2xl p-8 max-w-md w-full text-center border border-chat-border">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Error</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="bg-accent text-white px-6 py-3 rounded-xl font-semibold hover:bg-accent/80 transition-colors"
          >
            Back to Chat
          </button>
        </div>
      </div>
    )
  }

  // Payment result — success for cash/card or link for online
  if (result) {
    const step = result.step

    // Online → redirect to payment link
    if (step === 'awaiting_payment' && result.payment_link) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-chat-bg px-4">
          <div className="bg-chat-secondary rounded-2xl p-8 max-w-md w-full text-center border border-chat-border">
            <div className="w-16 h-16 bg-accent/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <CreditCard className="w-8 h-8 text-accent" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Complete Payment</h2>
            <p className="text-gray-400 mb-6">
              Click below to pay ₹{orderData.amount} via Razorpay
            </p>
            <a
              href={result.payment_link}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full bg-red-600 hover:bg-red-700 text-white px-6 py-4 rounded-xl font-bold transition-colors mb-4"
            >
              Pay ₹{orderData.amount} Now
            </a>
            <button
              onClick={() => navigate('/')}
              className="text-gray-400 hover:text-white text-sm transition-colors"
            >
              Back to Chat
            </button>
          </div>
        </div>
      )
    }

    // Cash or Card at Counter → confirmed
    return (
      <div className="min-h-screen flex items-center justify-center bg-chat-bg px-4">
        <div className="bg-chat-secondary rounded-2xl p-8 max-w-md w-full text-center border border-chat-border">
          <div className="w-16 h-16 bg-green-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Order Confirmed!</h2>
          <p className="text-gray-400 mb-2">
            Order <span className="text-white font-mono">{orderId}</span>
          </p>
          <p className="text-2xl font-bold text-green-400 mb-4">₹{orderData.amount}</p>
          <p className="text-gray-400 mb-6">
            {step === 'cash_selected'
              ? 'Pay with cash when you pick up your order.'
              : 'Pay with card at the counter when you arrive.'}
          </p>
          <button
            onClick={() => navigate('/')}
            className="w-full bg-accent text-white px-6 py-4 rounded-xl font-bold hover:bg-accent/80 transition-colors"
          >
            <ArrowLeft className="inline w-5 h-5 mr-2" />
            Back to Chat
          </button>
        </div>
      </div>
    )
  }

  // Main payment page — order summary + 3 buttons
  const items = orderData.items || []
  const methods = [
    { id: 'online', label: 'Pay Online', description: 'UPI, Card, Net Banking via Razorpay', icon: Smartphone, color: 'bg-blue-600' },
    { id: 'cash', label: 'Cash on Delivery', description: 'Pay when you pick up', icon: Wallet, color: 'bg-green-600' },
    { id: 'card_at_counter', label: 'Card at Counter', description: 'Pay by card when you arrive', icon: CreditCard, color: 'bg-purple-600' },
  ]

  return (
    <div className="min-h-screen bg-chat-bg">
      {/* Header */}
      <header className="bg-chat-secondary border-b border-chat-border px-5 py-4 flex items-center gap-3">
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-lg font-semibold text-white">Payment</h1>
      </header>

      <div className="max-w-lg mx-auto p-5 space-y-5">
        {/* Order Summary */}
        <div className="bg-chat-secondary rounded-2xl border border-chat-border overflow-hidden">
          <div className="px-5 py-4 border-b border-chat-border flex items-center gap-3">
            <ShoppingBag size={20} className="text-accent" />
            <h2 className="font-semibold text-white">Order Summary</h2>
            <span className="ml-auto text-xs text-gray-400 font-mono">{orderId}</span>
          </div>

          {items.length > 0 && (
            <div className="px-5 py-3 divide-y divide-chat-border/50">
              {items.map((item, i) => (
                <div key={i} className="flex justify-between py-2 text-sm">
                  <span className="text-gray-300">
                    {item.quantity || 1}x {item.name || item.item_name}
                  </span>
                  <span className="text-white font-medium">
                    ₹{((item.price || item.unit_price || 0) * (item.quantity || 1)).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          )}

          <div className="px-5 py-3 border-t border-chat-border space-y-1">
            {orderData.subtotal > 0 && (
              <div className="flex justify-between text-sm text-gray-400">
                <span>Subtotal</span>
                <span>₹{orderData.subtotal.toFixed(2)}</span>
              </div>
            )}
            {orderData.packaging_charges > 0 && (
              <div className="flex justify-between text-sm text-gray-400">
                <span>Packaging</span>
                <span>₹{orderData.packaging_charges.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-lg font-bold text-white pt-2">
              <span>Total</span>
              <span>₹{orderData.amount.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="bg-red-600/10 border border-red-500/30 rounded-xl p-4 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Payment Methods */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Select Payment Method</h3>
          {methods.map(method => {
            const Icon = method.icon
            return (
              <button
                key={method.id}
                onClick={() => handleSelectMethod(method.id)}
                disabled={selecting}
                className="w-full bg-chat-secondary hover:bg-chat-tertiary border border-chat-border rounded-xl p-4 flex items-center gap-4 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className={`w-12 h-12 ${method.color} rounded-xl flex items-center justify-center`}>
                  <Icon size={22} className="text-white" />
                </div>
                <div className="flex-1 text-left">
                  <h4 className="font-semibold text-white">{method.label}</h4>
                  <p className="text-sm text-gray-400">{method.description}</p>
                </div>
                {selecting && (
                  <Loader2 size={20} className="text-gray-400 animate-spin" />
                )}
              </button>
            )
          })}
        </div>

        {/* Security Note */}
        <p className="text-xs text-gray-500 text-center">
          Secure payment powered by Razorpay
        </p>
      </div>
    </div>
  )
}

export default PaymentPage

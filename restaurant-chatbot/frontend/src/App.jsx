import React, { useEffect, useRef, useCallback, useState } from 'react'
import { Wifi, WifiOff, Loader2 } from 'lucide-react'
import { useWebSocket, hasRecentSession, clearSession } from './hooks/useWebSocket'
import { useAGUI } from './hooks/useAGUI'
import {
  ChatMessage,
  CartCard,
  MenuCard,
  OrderCard,
  QuickReplies,
  FormCard,
  ActivityIndicator,
  ChatInput,
  SessionModal,
} from './components'

function App() {
  const chatContainerRef = useRef(null)
  const [showSessionModal, setShowSessionModal] = useState(false)
  const [sessionReady, setSessionReady] = useState(false)
  const sessionReadyRef = useRef(false)  // Ref to track sessionReady without causing reconnections

  const {
    messages,
    activity,
    isStreaming,
    handleEvent,
    addUserMessage,
    clearQuickReplies,
  } = useAGUI()

  // Keep ref in sync with state
  useEffect(() => {
    sessionReadyRef.current = sessionReady
  }, [sessionReady])

  // Stable event handler that checks sessionReady via ref (doesn't cause reconnection)
  // Auth form events (phone_auth, login_otp, name_collection) are always processed to ensure auth flow works
  const stableEventHandler = useCallback((event) => {
    // Always process auth-related forms (even before session modal is dismissed)
    const isAuthForm = event.type === 'FORM_REQUEST' &&
      (event.form_type === 'phone_auth' || event.form_type === 'login_otp' || event.form_type === 'name_collection')

    if (isAuthForm || sessionReadyRef.current) {
      handleEvent(event)
      // If auth form is received, auto-dismiss session modal and mark session ready
      if (isAuthForm && !sessionReadyRef.current) {
        setShowSessionModal(false)
        setSessionReady(true)
      }
    }
  }, [handleEvent])

  const { status, sendMessage, sendFormResponse } = useWebSocket(stableEventHandler)

  // Check for recent session on mount
  useEffect(() => {
    if (hasRecentSession()) {
      setShowSessionModal(true)
    } else {
      setSessionReady(true)
    }
  }, [])

  // Handle continuing previous session
  const handleContinueSession = useCallback(() => {
    setShowSessionModal(false)
    setSessionReady(true)
  }, [])

  // Handle starting new chat
  const handleNewChat = useCallback(() => {
    clearSession()
    setShowSessionModal(false)
    setSessionReady(true)
    window.location.reload()  // Reload to connect with new session ID
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages, activity])

  // Handle sending message
  const handleSendMessage = useCallback((message) => {
    addUserMessage(message)
    clearQuickReplies()
    sendMessage(message)
  }, [addUserMessage, clearQuickReplies, sendMessage])

  // Handle quick reply selection
  const handleQuickReply = useCallback((value) => {
    handleSendMessage(value)
  }, [handleSendMessage])

  // Handle form submission
  const handleFormSubmit = useCallback((formType, data) => {
    console.log('handleFormSubmit called:', { formType, data })
    sendFormResponse(formType, data)
  }, [sendFormResponse])

  // Handle adding items from MenuCard
  const handleAddToCart = useCallback((items) => {
    // Build a single message with all items
    const itemList = items.map(item => `${item.quantity} ${item.name}`).join(', ')
    const message = `Add to cart: ${itemList}`
    sendMessage(message)
  }, [sendMessage])

  // Render message based on type
  const renderMessage = (message) => {
    switch (message.type) {
      case 'cart':
        return <CartCard key={message.id} data={message.data} />
      case 'menu':
        return <MenuCard key={message.id} data={message.data} onAddToCart={handleAddToCart} />
      case 'order':
        return <OrderCard key={message.id} data={message.data} />
      case 'quick_replies':
        return (
          <QuickReplies
            key={message.id}
            options={message.data}
            onSelect={handleQuickReply}
          />
        )
      case 'form':
        return (
          <FormCard
            key={message.id}
            data={message.data}
            onSubmit={handleFormSubmit}
          />
        )
      default:
        return <ChatMessage key={message.id} message={message} />
    }
  }

  // Status indicator
  const StatusIndicator = () => {
    const config = {
      connected: { icon: Wifi, color: 'text-green-500', text: 'Connected' },
      connecting: { icon: Loader2, color: 'text-yellow-500', text: 'Connecting...', spin: true },
      disconnected: { icon: WifiOff, color: 'text-red-500', text: 'Disconnected' },
      error: { icon: WifiOff, color: 'text-red-500', text: 'Error' },
    }
    const { icon: Icon, color, text, spin } = config[status] || config.error

    return (
      <div className="flex items-center gap-2 text-sm">
        <Icon size={14} className={`${color} ${spin ? 'animate-spin' : ''}`} />
        <span className="text-gray-400">{text}</span>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-chat-bg">
      {/* Session Modal */}
      {showSessionModal && (
        <SessionModal
          onContinue={handleContinueSession}
          onNewChat={handleNewChat}
        />
      )}

      {/* Header */}
      <header className="bg-chat-secondary border-b border-chat-border px-5 py-3 flex items-center justify-between">
        <h1 className="text-base font-semibold">Restaurant AI Assistant</h1>
        <StatusIndicator />
      </header>

      {/* Chat Container */}
      <main
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto"
      >
        <div className="max-w-3xl mx-auto p-5 space-y-4">
          {/* Welcome Message */}
          {messages.length === 0 && !isStreaming && (
            <div className="text-center py-20">
              <h2 className="text-2xl font-semibold mb-4">Welcome! 👋</h2>
              <p className="text-gray-400 mb-6">
                I'm your AI restaurant assistant. I can help you with:
              </p>
              <ul className="text-gray-400 space-y-2 mb-8">
                <li>• Browse our menu and recommendations</li>
                <li>• Add items to your cart</li>
                <li>• Place orders for dine-in or takeaway</li>
                <li>• Track your order status</li>
              </ul>
              <QuickReplies
                options={['Show menu', 'View my cart', "What's popular?"]}
                onSelect={handleQuickReply}
              />
            </div>
          )}

          {/* Messages */}
          {messages.map(renderMessage)}

          {/* Activity Indicator */}
          {activity && <ActivityIndicator message={activity} />}
        </div>
      </main>

      {/* Input */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={status !== 'connected' || isStreaming || showSessionModal}
      />
    </div>
  )
}

export default App

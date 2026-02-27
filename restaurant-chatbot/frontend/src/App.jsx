import React, { useEffect, useRef, useCallback, useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Wifi, WifiOff, Loader2 } from 'lucide-react'
import { useWebSocket, hasRecentSession, clearSession } from './hooks/useWebSocket'
import { useAGUI } from './hooks/useAGUI'
import { useVoiceChat } from './hooks/useVoiceChat'
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
  PaymentSuccessCard,
  PaymentLinkCard,
  ReceiptCard,
  VoiceModeBanner,
} from './components'
import { SearchResultsCard } from './components/SearchResultsCard'
import PaymentSuccess from './components/PaymentSuccess'
import PaymentFailure from './components/PaymentFailure'

function ChatInterface() {
  const chatContainerRef = useRef(null)
  const [showSessionModal, setShowSessionModal] = useState(false)
  const [sessionReady, setSessionReady] = useState(false)
  const sessionReadyRef = useRef(false)  // Ref to track sessionReady without causing reconnections
  const [selectedLanguage, setSelectedLanguage] = useState("English")  // Language for chat responses

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
    console.log('🔶 stableEventHandler called:', event.type, event.form_type || '')

    // Always process auth-related forms (even before session modal is dismissed)
    const isAuthForm = event.type === 'FORM_REQUEST' &&
      (event.form_type === 'phone_auth' || event.form_type === 'login_otp' || event.form_type === 'name_collection')

    // Always process FORM_DISMISS for auth forms (needed to dismiss phone form after submission)
    const isAuthFormDismiss = event.type === 'FORM_DISMISS'

    // Always process payment-related events
    const isPaymentEvent = event.type === 'PAYMENT_LINK' || event.type === 'PAYMENT_SUCCESS'

    console.log('🔶 Event flags:', { isAuthForm, isAuthFormDismiss, isPaymentEvent, sessionReady: sessionReadyRef.current })

    if (isAuthForm || isAuthFormDismiss || isPaymentEvent || sessionReadyRef.current) {
      console.log('🟢 Processing event:', event.type)
      handleEvent(event)
      // If auth form is received, auto-dismiss session modal and mark session ready
      if (isAuthForm && !sessionReadyRef.current) {
        console.log('🟢 Auth form received, setting sessionReady=true')
        setShowSessionModal(false)
        setSessionReady(true)
      }
    } else {
      console.log('🔴 Event BLOCKED - sessionReady is false and not an auth event')
    }
  }, [handleEvent])

  const { status, sessionId, sendMessage, sendFormResponse } = useWebSocket(stableEventHandler)

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
    sendMessage(message, selectedLanguage)  // Pass language for response
  }, [addUserMessage, clearQuickReplies, sendMessage, selectedLanguage])

  // Handle quick reply selection
  const handleQuickReply = useCallback((value) => {
    // Map raw quick-reply actions to friendly display text
    const QUICK_REPLY_LABELS = {
      view_receipt: 'View Receipt',
      order_more: 'Order More',
    }
    const displayText = QUICK_REPLY_LABELS[value]
    if (displayText) {
      addUserMessage(displayText)
      clearQuickReplies()
      sendMessage(value, selectedLanguage)
    } else {
      handleSendMessage(value)
    }
  }, [handleSendMessage, addUserMessage, clearQuickReplies, sendMessage, selectedLanguage])

  // Handle checkout button click
  const handleCheckout = useCallback(() => {
    handleSendMessage('I want to checkout')
  }, [handleSendMessage])

  // Handle form submission
  const handleFormSubmit = useCallback((formType, data) => {
    console.log('handleFormSubmit called:', { formType, data })
    sendFormResponse(formType, data)
  }, [sendFormResponse])

  // Handle adding items from MenuCard/SearchResultsCard
  // Uses form_response to bypass LLM and directly call add_to_cart tool
  const handleAddToCart = useCallback((items) => {
    // Send as structured form_response for direct processing (no LLM interpretation)
    sendFormResponse('direct_add_to_cart', { items })

    // Also show user message for context
    const itemList = items.map(item => `${item.quantity}x ${item.name}`).join(', ')
    addUserMessage(`Adding to cart: ${itemList}`)
  }, [sendFormResponse, addUserMessage])

  // Handle cart quantity update from CartCard +/- buttons
  const handleCartUpdateQuantity = useCallback((itemName, newQuantity) => {
    sendFormResponse('direct_update_cart', { item_name: itemName, quantity: newQuantity })
  }, [sendFormResponse])

  // Handle cart item removal from CartCard delete button
  const handleCartRemoveItem = useCallback((itemName) => {
    sendFormResponse('direct_remove_from_cart', { item_name: itemName })
  }, [sendFormResponse])

  // Render message based on type
  const renderMessage = (message) => {
    console.log('renderMessage called for:', message.type, 'id:', message.id)
    switch (message.type) {
      case 'cart':
        return <CartCard key={message.id} data={message.data} onCheckout={handleCheckout} onUpdateQuantity={handleCartUpdateQuantity} onRemoveItem={handleCartRemoveItem} />
      case 'menu':
        return <MenuCard key={message.id} data={message.data} onAddToCart={handleAddToCart} />
      case 'search_results':
        return <SearchResultsCard key={message.id} data={message.data} onAddToCart={handleAddToCart} />
      case 'order':
        return <OrderCard key={message.id} data={message.data} />
      case 'payment_link':
        return <PaymentLinkCard key={message.id} data={message.data} />
      case 'receipt_link':
        return <ReceiptCard key={message.id} data={message.data} />
      case 'payment_success':
        console.log('Rendering PaymentSuccessCard with data:', message.data)
        return (
          <PaymentSuccessCard
            key={message.id}
            data={message.data}
            onQuickReply={handleQuickReply}
          />
        )
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

  // Voice Chat Hook Integration
  const {
    connect: connectVoice,
    toggleVoiceMode,
    stopAgentSpeech,
    voiceModeEnabled,
    isRecording: isVoiceRecording,
    isProcessing: isVoiceProcessing,
    isUserSpeaking,
    isAISpeaking,
    isConnected: isVoiceConnected,
    transcript,
    responseText
  } = useVoiceChat(sessionId, stableEventHandler) // Use same session ID + AG-UI handler as chat

  // Auto-connect voice when language changes or session is ready
  useEffect(() => {
    if (sessionReady) {
      // Connect to voice socket with selected language
      // We disconnect/reconnect to update the System Prompt with the new language
      connectVoice(selectedLanguage);
    }
  }, [sessionReady, selectedLanguage, connectVoice]);

  // Track previous transcript/response to detect changes
  const prevTranscriptRef = useRef('');
  const prevResponseRef = useRef('');

  // Add voice transcripts to chat messages
  useEffect(() => {
    if (voiceModeEnabled && transcript && transcript !== prevTranscriptRef.current) {
      prevTranscriptRef.current = transcript;
      addUserMessage(transcript);
    }
  }, [voiceModeEnabled, transcript, addUserMessage]);

  // Add voice AI responses to chat messages
  useEffect(() => {
    if (voiceModeEnabled && responseText && responseText !== prevResponseRef.current) {
      prevResponseRef.current = responseText;
      // Add AI response via AGUI events
      handleEvent({ type: 'TEXT_MESSAGE_START', message_id: `voice_${Date.now()}`, role: 'assistant' });
      handleEvent({ type: 'TEXT_MESSAGE_CONTENT', delta: responseText });
      handleEvent({ type: 'TEXT_MESSAGE_END' });
    }
  }, [voiceModeEnabled, responseText, handleEvent]);

  // Clear voice refs when exiting voice mode
  useEffect(() => {
    if (!voiceModeEnabled) {
      prevTranscriptRef.current = '';
      prevResponseRef.current = '';
    }
  }, [voiceModeEnabled]);


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

      {/* Voice Mode Banner (shown when voice mode is active) */}
      {voiceModeEnabled && (
        <VoiceModeBanner
          isRecording={isVoiceRecording}
          isProcessing={isVoiceProcessing}
          isUserSpeaking={isUserSpeaking}
          isAISpeaking={isAISpeaking}
          onExitVoiceMode={toggleVoiceMode}
          onStopAgent={stopAgentSpeech}
        />
      )}

      {/* Chat Container - Always visible */}
      <main
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto"
      >
        <div className="max-w-3xl mx-auto p-5 space-y-4">
          {/* Welcome Message */}
          {messages.length === 0 && !isStreaming && (
            <div className="text-center py-20">
              <h2 className="text-2xl font-semibold mb-4">Welcome!</h2>
              <p className="text-gray-400 mb-6">
                I'm your AI restaurant assistant. I can help you with:
              </p>
              <ul className="text-gray-400 space-y-2 mb-8">
                <li>Browse our menu and recommendations</li>
                <li>Add items to your cart</li>
                <li>Place takeaway orders</li>
                <li>Track your order status</li>
              </ul>
              <QuickReplies
                options={['Show menu', 'View my cart', "What's popular?"]}
                onSelect={handleQuickReply}
              />
            </div>
          )}

          {/* Messages */}
          {console.log('Rendering messages array, length:', messages.length, 'types:', messages.map(m => m.type))}
          {messages.map(renderMessage)}

          {/* Activity Indicator */}
          {activity && <ActivityIndicator message={activity} />}
        </div>
      </main>

      {/* Input */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={status !== 'connected' || isStreaming || showSessionModal}

        // Voice Props
        onToggleVoiceMode={toggleVoiceMode}
        voiceModeActive={voiceModeEnabled}
        selectedLanguage={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
      />
    </div>
  )
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/payment/success" element={<PaymentSuccess />} />
        <Route path="/payment/failure" element={<PaymentFailure />} />
        <Route path="/" element={<ChatInterface />} />
      </Routes>
    </Router>
  );
}

export default App

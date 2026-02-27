import { useState, useEffect, useCallback, useRef } from 'react'

const SESSION_TIMEOUT_MS = 30 * 60 * 1000  // 30 minutes

const generateNewSessionId = () => {
  return 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36)
}

// Store current page's sessionId (generated fresh on each page load)
let currentPageSessionId = null

const getSessionId = () => {
  // Always generate a NEW sessionId on page load (hard reload = fresh start)
  // This ensures users go through auth again after F5/refresh
  if (!currentPageSessionId) {
    currentPageSessionId = generateNewSessionId()
    sessionStorage.setItem('sessionId', currentPageSessionId)
  }
  return currentPageSessionId
}

const updateLastActivity = () => {
  sessionStorage.setItem('sessionLastActivity', Date.now().toString())
}

// Check if there's an existing session that's still within the timeout window
export const hasRecentSession = () => {
  const sessionId = sessionStorage.getItem('sessionId')
  const lastActivity = sessionStorage.getItem('sessionLastActivity')

  if (!sessionId || !lastActivity) {
    return false
  }

  const timeSinceActivity = Date.now() - parseInt(lastActivity, 10)
  return timeSinceActivity < SESSION_TIMEOUT_MS
}

// Clear current session and create a new one
export const clearSession = () => {
  sessionStorage.removeItem('sessionId')
  sessionStorage.removeItem('sessionLastActivity')
  const newSessionId = generateNewSessionId()
  sessionStorage.setItem('sessionId', newSessionId)
  return newSessionId
}

export const useWebSocket = (onEvent) => {
  const [status, setStatus] = useState('connecting')
  const [sessionId] = useState(getSessionId)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const receivedStreamingRef = useRef(false)  // Track if we received AGUI streaming
  const mountedRef = useRef(true)  // Track if component is mounted
  const connectionIdRef = useRef(0)  // Track connection ID to ignore stale callbacks

  const connect = useCallback(() => {
    // Prevent duplicate connections
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
      console.log('WebSocket already connected or connecting, skipping duplicate connection')
      return
    }

    // Don't connect if component was unmounted (StrictMode cleanup)
    if (!mountedRef.current) {
      console.log('Component unmounted, skipping connection')
      return
    }

    // Increment connection ID to invalidate any pending callbacks from old connections
    const currentConnectionId = ++connectionIdRef.current

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    // Backend WebSocket endpoint is at /api/v1/chat/{session_id}
    const wsUrl = `${protocol}//${host}/api/v1/chat/${sessionId}`

    setStatus('connecting')

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        // Ignore if this is a stale connection or component unmounted
        if (connectionIdRef.current !== currentConnectionId || !mountedRef.current) {
          console.log('Stale or unmounted WebSocket connection, closing')
          ws.close()
          return
        }
        setStatus('connected')
        console.log('WebSocket connected')
      }

      ws.onclose = () => {
        // Only reconnect if this is the current connection and still mounted
        if (connectionIdRef.current !== currentConnectionId || !mountedRef.current) {
          return
        }
        setStatus('disconnected')
        console.log('WebSocket disconnected')
        // Reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, 3000)
      }

      ws.onerror = (error) => {
        if (connectionIdRef.current === currentConnectionId && mountedRef.current) {
          console.error('WebSocket error:', error)
          setStatus('error')
        }
      }

      ws.onmessage = (event) => {
        // Ignore messages from stale connections
        if (connectionIdRef.current !== currentConnectionId || !mountedRef.current) {
          return
        }

        try {
          const data = JSON.parse(event.data)
          console.log('🔵 WS MESSAGE RECEIVED:', data.message_type, data)

          // Extract AGUI event from nested structure
          // Check both metadata and debug_metadata for agui data
          const agui = data.debug_metadata?.agui || data.metadata?.agui

          // Debug: Log FORM_REQUEST specifically
          if (agui?.type === 'FORM_REQUEST') {
            console.log('🟢 AUTH FORM RECEIVED:', agui.form_type, agui)
          }

          if (data.message_type === 'agui_event' && agui) {
            // Track if we received streaming text via AGUI
            if (agui.type === 'TEXT_MESSAGE_START') {
              receivedStreamingRef.current = true
            } else if (agui.type === 'TEXT_MESSAGE_END') {
              // Reset flag when stream ends so we don't block future legacy messages
              // Wait a tick to ensure any racing ai_response is handled
              setTimeout(() => {
                receivedStreamingRef.current = false
              }, 100)
            }
            // DON'T reset on RUN_FINISHED - ai_response comes AFTER it
            // Flag is reset only after ai_response is processed
            // Pass the AGUI event directly to handler
            console.log('AGUI detected:', agui)
            onEvent(agui)
          } else if (data.message_type === 'ai_response' && data.message) {
            updateLastActivity()  // Track activity on AI response
            // Only use ai_response as fallback if we didn't receive AGUI streaming
            if (!receivedStreamingRef.current) {
              console.log('AI Response (fallback):', data.message)
              // Dispatch as a complete text message
              onEvent({ type: 'TEXT_MESSAGE_START', message_id: Date.now().toString(), role: 'assistant' })
              onEvent({ type: 'TEXT_MESSAGE_CONTENT', delta: data.message })
              onEvent({ type: 'TEXT_MESSAGE_END' })
            } else {
              console.log('AI Response (skipped - already streamed):', data.message)
            }
            // Reset flag after processing ai_response
            receivedStreamingRef.current = false
          } else if (data.message_type === 'quick_replies' && data.quick_replies) {
            onEvent({ type: 'QUICK_REPLIES', options: data.quick_replies })
          } else if (data.message_type === 'typing_indicator') {
            // Ignore typing indicators
          } else if (data.type) {
            // Direct event format
            onEvent(data)
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      if (mountedRef.current) {
        setStatus('error')
      }
    }
  }, [sessionId, onEvent])

  useEffect(() => {
    // Reset mounted flag for new mount (handles StrictMode remount)
    mountedRef.current = true
    connect()

    return () => {
      // Mark as unmounted FIRST to prevent any pending callbacks
      mountedRef.current = false

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  const sendMessage = useCallback((message, language = 'English') => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      updateLastActivity()  // Track activity on message send
      wsRef.current.send(JSON.stringify({
        type: 'user_message',
        content: message,
        session_id: sessionId,
        language: language,  // Pass language preference for response
      }))
      return true
    }
    return false
  }, [sessionId])

  const sendFormResponse = useCallback((formType, data) => {
    console.log('sendFormResponse called:', { formType, data, wsState: wsRef.current?.readyState })
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload = {
        type: 'form_response',
        form_type: formType,
        data: data,
        session_id: sessionId,
      }
      console.log('Sending form_response:', payload)
      wsRef.current.send(JSON.stringify(payload))
      return true
    }
    console.error('WebSocket not open, cannot send form_response')
    return false
  }, [sessionId])

  return {
    status,
    sessionId,
    sendMessage,
    sendFormResponse,
  }
}

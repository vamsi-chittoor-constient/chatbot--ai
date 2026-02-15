import { useReducer, useCallback } from 'react'

const initialState = {
  messages: [],
  activity: null,
  isStreaming: false,
  currentStreamId: null,
}

function aguiReducer(state, action) {
  switch (action.type) {
    case 'ADD_USER_MESSAGE':
      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies'), {
          id: Date.now(),
          role: 'user',
          content: action.payload,
          timestamp: new Date(),
        }],
      }

    case 'RUN_STARTED':
      return {
        ...state,
        isStreaming: true,
        activity: null,
      }

    case 'RUN_FINISHED':
    case 'RUN_ERROR':
      return {
        ...state,
        isStreaming: false,
        activity: null,
        currentStreamId: null,
      }

    case 'ACTIVITY_START':
      // Ignore late ACTIVITY_START after RUN_FINISHED (isStreaming is false)
      if (!state.isStreaming) return state
      return {
        ...state,
        activity: action.payload.message || action.payload.activity || 'Processing...',
      }

    case 'ACTIVITY_END':
      return {
        ...state,
        activity: null,
      }

    case 'TEXT_MESSAGE_START':
      const newStreamId = Date.now()
      return {
        ...state,
        currentStreamId: newStreamId,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies'), {
          id: newStreamId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true,
        }],
      }

    case 'TEXT_MESSAGE_CONTENT':
      const content = action.payload.delta || action.payload.content || ''
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === state.currentStreamId
            ? { ...msg, content: msg.content + content }
            : msg
        ),
      }

    case 'TEXT_MESSAGE_END':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === state.currentStreamId
            ? { ...msg, isStreaming: false }
            : msg
        ),
      }

    case 'CART_DATA': {
      const newCartData = {
        items: action.payload.items,
        total: action.payload.total,
        packaging_charge_per_item: action.payload.packaging_charge_per_item || 30,
      }
      // Always place cart at the bottom — remove old cart and append fresh
      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'cart' && msg.type !== 'quick_replies'), {
          id: Date.now(),
          role: 'system',
          type: 'cart',
          data: newCartData,
          timestamp: new Date(),
        }],
      }
    }

    case 'MENU_DATA':
      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies'), {
          id: Date.now(),
          role: 'system',
          type: 'menu',
          data: {
            items: action.payload.items,
            categories: action.payload.categories,
          },
          timestamp: new Date(),
        }],
      }

    case 'SEARCH_RESULTS':
      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies' && msg.type !== 'search_results'), {
          id: Date.now(),
          role: 'system',
          type: 'search_results',
          data: {
            query: action.payload.query,
            items: action.payload.items,
            currentMealPeriod: action.payload.current_meal_period,
            availableCount: action.payload.available_count,
            unavailableCount: action.payload.unavailable_count,
          },
          timestamp: new Date(),
        }],
      }

    case 'ORDER_DATA':
      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies'), {
          id: Date.now(),
          role: 'system',
          type: 'order',
          data: action.payload.order || action.payload,
          timestamp: new Date(),
        }],
      }

    case 'QUICK_REPLIES':
      // Clear any EXISTING quick replies before adding new ones
      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies'), {
          id: Date.now(),
          role: 'system',
          type: 'quick_replies',
          data: action.payload.options || action.payload.replies || action.payload,
          timestamp: new Date(),
        }],
      }

    case 'PAYMENT_LINK':
      console.log('REDUCER: PAYMENT_LINK', action.payload)
      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies'), {
          id: Date.now(),
          role: 'system',
          type: 'payment_link',
          data: {
            payment_link: action.payload.payment_link,
            amount: action.payload.amount,
            expires_at: action.payload.expires_at,
          },
          timestamp: new Date(),
        }],
      }

    case 'PAYMENT_SUCCESS':
      console.log('REDUCER: PAYMENT_SUCCESS', action.payload)
      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies'), {
          id: Date.now(),
          role: 'system',
          type: 'payment_success',
          data: {
            order_id: action.payload.order_id,
            order_number: action.payload.order_number,
            amount: action.payload.amount,
            payment_id: action.payload.payment_id,
            order_type: action.payload.order_type,
            quick_replies: action.payload.quick_replies || [],
          },
          timestamp: new Date(),
        }],
      }

    case 'RECEIPT_LINK':
      console.log('REDUCER: RECEIPT_LINK', action.payload)
      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies'), {
          id: Date.now(),
          role: 'system',
          type: 'receipt_link',
          data: {
            order_number: action.payload.order_number,
            amount: action.payload.amount,
            download_url: action.payload.download_url,
            items: action.payload.items || [],
          },
          timestamp: new Date(),
        }],
      }

    case 'FORM_REQUEST':
      // Mark auth forms as ephemeral so they don't persist in chat history
      const isAuthForm = ['phone_auth', 'login_otp', 'name_collection'].includes(action.payload.form_type)

      // Check if form of same type already exists to prevent duplicates
      const existingFormIndex = state.messages.findIndex(
        msg => msg.type === 'form' && msg.data?.formType === action.payload.form_type
      )

      // If form already exists, don't add duplicate
      if (existingFormIndex !== -1) {
        return state
      }

      return {
        ...state,
        messages: [...state.messages.filter(msg => msg.type !== 'quick_replies'), {
          id: Date.now(),
          role: 'system',
          type: 'form',
          ephemeral: isAuthForm,  // Mark auth forms as ephemeral
          data: {
            formType: action.payload.form_type,
            fields: action.payload.fields,
            title: action.payload.title,
            description: action.payload.description,
            submit_label: action.payload.submit_label,
            cancel_label: action.payload.cancel_label,
            metadata: action.payload.metadata,
          },
          timestamp: new Date(),
        }],
      }

    case 'FORM_DISMISS':
      // Remove forms of specified type(s) from messages
      const formTypesToDismiss = action.payload.form_types || [action.payload.form_type]
      return {
        ...state,
        messages: state.messages.filter(msg => {
          // Remove forms that match the dismiss types
          if (msg.type === 'form' && formTypesToDismiss.includes(msg.data?.formType)) {
            return false
          }
          // Also remove any ephemeral forms (safety cleanup for auth forms)
          if (msg.type === 'form' && msg.ephemeral) {
            return false
          }
          return true
        }),
      }

    case 'CLEAR_QUICK_REPLIES':
      return {
        ...state,
        messages: state.messages.filter(msg => msg.type !== 'quick_replies'),
      }

    default:
      return state
  }
}

export const useAGUI = () => {
  const [state, dispatch] = useReducer(aguiReducer, initialState)

  const handleEvent = useCallback((event) => {
    console.log('AGUI Event:', event)
    const { type, ...payload } = event
    console.log('Dispatching:', type, payload)
    dispatch({ type, payload })
  }, [])

  const addUserMessage = useCallback((content) => {
    dispatch({ type: 'ADD_USER_MESSAGE', payload: content })
  }, [])

  const clearQuickReplies = useCallback(() => {
    dispatch({ type: 'CLEAR_QUICK_REPLIES' })
  }, [])

  return {
    ...state,
    handleEvent,
    addUserMessage,
    clearQuickReplies,
  }
}

import React, { useState } from 'react'
import { CreditCard, KeyRound, Send, Phone, UserCheck, User } from 'lucide-react'

export const FormCard = ({ data, onSubmit, onCancel }) => {
  const { formType, fields, title: customTitle, description, submit_label, cancel_label } = data
  const [formData, setFormData] = useState({})

  const handleChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    console.error('🔥 FormCard submit triggered via form onSubmit')
    console.log('FormCard submit details:', { formType, formData, onSubmit: typeof onSubmit })
    if (onSubmit) {
      try {
        onSubmit(formType, formData)
        console.error('🔥 onSubmit prop executed successfully')
      } catch (err) {
        console.error('🔥 CRITICAL: Error executing onSubmit prop:', err)
      }
    } else {
      console.error('🔥 CRITICAL: FormCard: onSubmit prop is not defined!')
    }
  }

  const handleCancel = () => {
    if (onCancel) {
      onCancel(formType)
    } else {
      // Send cancel response to backend
      onSubmit(formType, { cancelled: true })
    }
  }

  const getTitle = () => {
    if (customTitle) {
      // Map form types to icons
      const iconMap = {
        'phone_auth': Phone,
        'login_otp': KeyRound,
        'name_collection': User,
        'payment_card': CreditCard,
        'otp_verify': KeyRound,
        'payment': CreditCard,
        'otp': KeyRound,
      }
      return { icon: iconMap[formType] || Send, text: customTitle }
    }

    switch (formType) {
      case 'payment':
      case 'payment_card':
        return { icon: CreditCard, text: 'Payment Details' }
      case 'otp':
      case 'otp_verify':
      case 'login_otp':
        return { icon: KeyRound, text: 'Enter OTP' }
      case 'phone_auth':
        return { icon: Phone, text: 'Welcome!' }
      default:
        return { icon: Send, text: 'Enter Details' }
    }
  }

  const getDefaultFields = () => {
    if (fields && fields.length > 0) return fields

    switch (formType) {
      case 'otp':
      case 'otp_verify':
      case 'login_otp':
        return [{ name: 'otp', label: 'OTP Code', type: 'text', placeholder: 'Enter 6-digit OTP', maxLength: 6 }]
      case 'phone':
      case 'phone_auth':
        return [{ name: 'phone', label: 'Mobile Number', type: 'tel', placeholder: '+91 XXXXX XXXXX' }]
      default:
        return [{ name: 'value', label: 'Value', type: 'text', placeholder: 'Enter value' }]
    }
  }

  const getSubmitLabel = () => {
    if (submit_label) return submit_label
    switch (formType) {
      case 'phone_auth': return 'Continue'
      case 'login_otp': return 'Verify'
      case 'payment_card': return 'Pay Now'
      case 'otp_verify': return 'Verify & Pay'
      default: return 'Submit'
    }
  }

  const { icon: Icon, text: title } = getTitle()
  const formFields = getDefaultFields()
  const showCancel = cancel_label && cancel_label.length > 0

  return (
    <div className="bg-chat-secondary border border-chat-border rounded-xl p-5 animate-fadeIn">
      <div className="flex items-center gap-2 font-semibold text-[15px] mb-2">
        <Icon size={18} className="text-accent" />
        <span>{title}</span>
      </div>

      {description && (
        <p className="text-sm text-gray-400 mb-4">{description}</p>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {formFields.map((field, index) => (
          <div key={index}>
            <label className="block text-sm text-gray-400 mb-1.5">
              {field.label}
            </label>
            <input
              type={field.type === 'otp' ? 'text' : (field.type || 'text')}
              name={field.name}
              placeholder={field.placeholder || ''}
              value={formData[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              maxLength={field.maxLength}
              minLength={field.minLength}
              className="w-full px-3 py-2.5 bg-chat-bg border border-chat-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
              required={field.required !== false}
              autoFocus={index === 0}
            />
          </div>
        ))}

        <div className={`flex gap-3 ${showCancel ? '' : 'flex-col'}`}>
          <button
            type="submit"
            onClick={() => console.error('🔥 Submit button CLICKED manually')}
            className="flex-1 py-3 bg-accent hover:bg-accent-hover text-white font-semibold rounded-lg transition-colors"
          >
            {getSubmitLabel()}
          </button>

          {showCancel && (
            <button
              type="button"
              onClick={handleCancel}
              className="px-4 py-3 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
            >
              {cancel_label}
            </button>
          )}
        </div>
      </form>
    </div>
  )
}

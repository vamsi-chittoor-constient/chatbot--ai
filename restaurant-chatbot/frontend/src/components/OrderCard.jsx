import React from 'react'
import { Package, Clock, CheckCircle, AlertCircle } from 'lucide-react'

const statusConfig = {
  confirmed: { color: 'bg-green-900 text-green-300', icon: CheckCircle },
  preparing: { color: 'bg-yellow-900 text-yellow-300', icon: Clock },
  ready: { color: 'bg-blue-900 text-blue-300', icon: Package },
  cancelled: { color: 'bg-red-900 text-red-300', icon: AlertCircle },
  default: { color: 'bg-gray-700 text-gray-300', icon: Package },
}

export const OrderCard = ({ data }) => {
  const order = data || {}
  const status = (order.status || 'confirmed').toLowerCase()
  const config = statusConfig[status] || statusConfig.default
  const StatusIcon = config.icon

  return (
    <div className="bg-chat-secondary border border-chat-border rounded-xl p-4 animate-fadeIn">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 font-semibold text-[15px]">
          <Package size={18} className="text-accent" />
          <span>Order #{order.order_id || order.id || 'N/A'}</span>
        </div>
        <span className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold uppercase ${config.color}`}>
          <StatusIcon size={12} />
          {order.status || 'Confirmed'}
        </span>
      </div>

      {order.items && order.items.length > 0 && (
        <div className="text-gray-400 text-sm mb-3">
          {order.items.map((item, i) => (
            <span key={i}>
              {item.name} x{item.quantity}
              {i < order.items.length - 1 ? ', ' : ''}
            </span>
          ))}
        </div>
      )}

      <div className="flex justify-between items-center pt-3 border-t border-chat-border">
        <span className="text-gray-400 text-sm">
          Takeaway
        </span>
        <span className="font-semibold text-accent">
          Total: Rs.{order.total || 0}
        </span>
      </div>
    </div>
  )
}

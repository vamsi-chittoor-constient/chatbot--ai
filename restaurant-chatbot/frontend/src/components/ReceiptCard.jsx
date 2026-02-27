import React from 'react'
import { FileText, Download } from 'lucide-react'

export function ReceiptCard({ data }) {
  const { order_number, amount, download_url, items = [] } = data

  return (
    <div className="mb-6 animate-fadeIn">
      {/* Header */}
      <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-t-2xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
            <FileText className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-xl font-bold">Order Receipt</h3>
            <p className="text-blue-100 text-sm">Order #{order_number}</p>
          </div>
        </div>
      </div>

      {/* Items + Download */}
      <div className="bg-chat-assistant rounded-b-2xl p-6 border border-gray-700/50">
        {/* Item List */}
        {items.length > 0 && (
          <div className="space-y-2 mb-4">
            {items.map((item, idx) => (
              <div key={idx} className="flex justify-between items-center py-2 border-b border-gray-700/30">
                <span className="text-gray-300 text-sm">
                  {item.quantity}x {item.name}
                </span>
                <span className="text-gray-300 text-sm font-medium">
                  ₹{(item.price * item.quantity).toFixed(0)}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Total */}
        <div className="flex justify-between items-center py-3 mb-5 border-t border-gray-600/50">
          <span className="text-white font-semibold">Total</span>
          <span className="text-green-400 font-bold text-lg">₹{amount}</span>
        </div>

        {/* Download Button */}
        <a
          href={download_url}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 px-6 rounded-xl transition-all duration-200 shadow-md hover:shadow-lg hover:scale-[1.01] active:scale-[0.99]"
        >
          <Download size={18} />
          Download PDF Receipt
        </a>
      </div>
    </div>
  )
}

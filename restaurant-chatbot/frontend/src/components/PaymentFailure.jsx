import React from 'react';
import { XCircle, AlertTriangle } from 'lucide-react';

function PaymentFailure() {
    // You can get URL params if needed: ?reason=failed_verification

    // Simple modern UI for failure
    const colors = {
        bg: 'bg-red-50',
        icon: 'text-red-500',
        title: 'text-red-700',
        button: 'bg-red-600 hover:bg-red-700'
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-chat-bg p-4">
            <div className="bg-white rounded-2xl shadow-xl max-w-sm w-full p-8 text-center border border-red-100">
                <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse-slow">
                    <AlertTriangle className={`w-10 h-10 ${colors.icon}`} strokeWidth={2} />
                </div>

                <h1 className="text-2xl font-bold text-gray-900 mb-2">Payment Failed</h1>
                <p className="text-gray-500 mb-8 leading-relaxed">
                    We couldn't process your payment. This could be due to a network issue or declined transaction.
                </p>

                <div className="bg-gray-50 rounded-xl p-4 mb-8 text-left border border-gray-100">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">WHAT YOU CAN DO</p>
                    <ul className="text-sm text-gray-600 space-y-1">
                        <li>• Return to chat and try payment again</li>
                        <li>• Contact support for assistance</li>
                        <li>• Request a new payment link</li>
                    </ul>
                </div>

                <div className="flex flex-col gap-3">
                    <button
                        onClick={() => window.close()}
                        className={`${colors.button} text-white px-8 py-3 rounded-xl font-semibold transition-colors`}
                    >
                        Close Window
                    </button>
                    <a
                        href="/"
                        className="text-gray-600 hover:text-gray-800 text-sm font-medium transition-colors"
                    >
                        Return to Chat
                    </a>
                </div>
            </div>
        </div>
    );
}

export default PaymentFailure;

import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';

function PaymentSuccess() {
    const [searchParams] = useSearchParams();
    const [status, setStatus] = useState('verifying');
    const paymentId = searchParams.get('payment_id');
    const orderId = searchParams.get('order_id');
    const signature = searchParams.get('signature');

    const paymentStatus = searchParams.get('status');

    useEffect(() => {
        // If we have direct status from URL (for simple testing or certain flows)
        if (paymentStatus) {
            if (paymentStatus === 'success') {
                setStatus('success');
            } else {
                setStatus('failed');
            }
            return;
        }

        // Otherwise verify with backend if we have payment details
        if (paymentId && orderId && signature) {
            verifyPayment();
        } else {
            // Missing parameters
            setStatus('failed');
        }
    }, [paymentId, orderId, signature, paymentStatus]);

    const verifyPayment = async () => {
        try {
            // In a real app, you would call your backend here to verify the signature
            // const response = await fetch('/api/v1/payment/verify', { ... });

            // For this demo/prototype, we'll simulate verification success
            setTimeout(() => {
                setStatus('success');
            }, 1500);
        } catch (error) {
            console.error('Verification failed:', error);
            setStatus('failed');
        }
    };

    if (status === 'verifying') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-chat-bg">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-12 h-12 text-accent animate-spin" />
                    <p className="text-gray-400 text-lg">Verifying payment...</p>
                </div>
            </div>
        );
    }

    if (status === 'success') {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-green-900 to-green-950 px-4">
                <div className="bg-white rounded-3xl shadow-2xl p-12 max-w-md w-full text-center animate-fade-in relative overflow-hidden">
                    {/* Success Background Pattern */}
                    <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-green-400 to-emerald-500"></div>

                    <div className="mb-8 relative">
                        <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                            <CheckCircle className="w-12 h-12 text-green-600" strokeWidth={3} />
                        </div>
                        <h1 className="text-3xl font-extrabold text-gray-900 mb-2">Payment Successful!</h1>
                        <p className="text-gray-500 font-medium">Thank you for your order</p>
                    </div>

                    <div className="bg-gray-50 rounded-2xl p-6 mb-8 border border-gray-100">
                        <div className="flex justify-between items-center mb-3 pb-3 border-b border-gray-200">
                            <span className="text-gray-500 text-sm">Payment ID</span>
                            <span className="text-gray-900 font-mono text-sm">{paymentId || 'PAY-123456'}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-500 text-sm">Order ID</span>
                            <span className="text-gray-900 font-mono text-sm">{orderId || 'ORD-789012'}</span>
                        </div>
                    </div>

                    <p className="text-gray-600 mb-8 leading-relaxed text-sm">
                        Your transaction has been completed successfully. You can now close this window and return to the chat.
                    </p>

                    <button
                        onClick={() => window.close()}
                        className="w-full bg-gray-900 text-white px-8 py-4 rounded-xl font-bold hover:bg-gray-800 transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-gray-200"
                    >
                        Close Window
                    </button>
                </div>
            </div>
        );
    }

    // Other statuses (cancelled, failed, etc.)
    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-yellow-600 to-orange-700">
            <div className="bg-white rounded-3xl shadow-2xl p-12 max-w-md w-full text-center animate-fade-in">
                <XCircle className="w-20 h-20 mx-auto text-yellow-600 mb-6" />
                <h1 className="text-3xl font-bold text-gray-800 mb-4">Payment {paymentStatus}</h1>
                <p className="text-gray-600 mb-6">
                    Your payment was not completed. Please try again or contact support.
                </p>
                <button
                    onClick={() => window.close()}
                    className="bg-yellow-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-yellow-700 transition-colors"
                >
                    Close Window
                </button>
            </div>
        </div>
    );
}

export default PaymentSuccess;

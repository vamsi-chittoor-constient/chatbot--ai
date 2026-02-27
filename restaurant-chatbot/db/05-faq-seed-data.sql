-- FAQ Seed Data
-- Provides sample frequently asked questions for the chatbot FAQ system
-- Categories: delivery, payment, ordering, refunds, account, general

-- Clear existing test data (optional, for clean slate)
-- DELETE FROM faq WHERE 1=1;

-- Insert sample FAQ categories and questions
INSERT INTO faq (question, answer, category, keywords, priority, is_active) VALUES
-- Delivery FAQs (High Priority)
('What are your delivery hours?', 'We deliver from 9 AM to 11 PM every day, including weekends and holidays.', 'delivery', ARRAY['delivery', 'hours', 'time', 'open'], 10, true),
('What is the delivery fee?', 'Delivery is FREE for orders above Rs.299. For orders below Rs.299, a delivery fee of Rs.40 applies.', 'delivery', ARRAY['delivery', 'fee', 'charge', 'cost', 'free'], 10, true),
('How long does delivery take?', 'Most deliveries arrive within 30-45 minutes. We''ll give you real-time updates on your order status.', 'delivery', ARRAY['delivery', 'time', 'how long', 'eta', 'fast'], 9, true),
('What is your delivery area?', 'We deliver within a 10 km radius of our restaurant. Enter your address during checkout to check if we deliver to your location.', 'delivery', ARRAY['delivery', 'area', 'location', 'where'], 8, true),
('Can I schedule a delivery for later?', 'Yes! You can schedule deliveries up to 24 hours in advance. Just let us know your preferred time.', 'delivery', ARRAY['delivery', 'schedule', 'advance', 'later', 'preorder'], 7, true),

-- Payment FAQs (High Priority)
('What payment methods do you accept?', 'We accept credit/debit cards (Visa, Mastercard, Amex), UPI, net banking, digital wallets, and cash on delivery.', 'payment', ARRAY['payment', 'methods', 'card', 'upi', 'cod', 'cash'], 10, true),
('Is online payment safe?', 'Yes! All online payments are processed through secure, PCI-compliant payment gateways with 256-bit encryption. Your card details are never stored on our servers.', 'payment', ARRAY['payment', 'safe', 'security', 'secure', 'encryption'], 8, true),
('Can I pay with cash?', 'Yes, we accept cash on delivery for all orders. Please keep exact change if possible.', 'payment', ARRAY['payment', 'cash', 'cod', 'cash on delivery'], 7, true),
('Do you accept UPI payments?', 'Yes! We accept all major UPI apps including Google Pay, PhonePe, Paytm, and BHIM.', 'payment', ARRAY['payment', 'upi', 'gpay', 'phonepe', 'paytm'], 7, true),
('Can I split payment between card and cash?', 'Currently, we don''t support split payments. You can pay the full amount using one payment method.', 'payment', ARRAY['payment', 'split', 'multiple', 'partial'], 5, true),

-- Order FAQs (High Priority)
('How do I track my order?', 'After placing your order, you''ll receive a confirmation with order ID. Just ask me "what''s my order status" or "track my order" and I''ll give you real-time updates!', 'ordering', ARRAY['track', 'status', 'order', 'where'], 10, true),
('Can I cancel my order?', 'Yes, you can cancel within 5 minutes of placing the order for a full refund. After that, please contact our support team as the kitchen may have started preparing your food.', 'ordering', ARRAY['cancel', 'cancellation', 'remove'], 9, true),
('Can I modify my order after placing it?', 'Orders can be modified within 5 minutes of placement. After that, the kitchen may have already started preparing your food. Contact support for urgent changes.', 'ordering', ARRAY['modify', 'change', 'edit', 'update'], 8, true),
('What is your minimum order value?', 'Our minimum order value is Rs.99 for delivery. There''s no minimum for dine-in or takeaway orders.', 'ordering', ARRAY['minimum', 'order', 'value', 'amount'], 7, true),
('Do I need to create an account to order?', 'No, you can order as a guest. However, creating an account lets you save addresses, track order history, and earn loyalty rewards!', 'ordering', ARRAY['account', 'guest', 'register', 'login'], 6, true),
('How do I add special instructions?', 'You can add special instructions for each item (like "no onions" or "extra spicy") or for the whole order during checkout. Just tell me your preferences!', 'ordering', ARRAY['instructions', 'special', 'request', 'customize'], 7, true),

-- Refund FAQs (High Priority)
('What is your refund policy?', 'If you''re not satisfied with your order, contact us within 24 hours. We offer full refunds for quality issues, incorrect orders, or delivery problems.', 'refunds', ARRAY['refund', 'policy', 'money back', 'return'], 10, true),
('How long do refunds take?', 'Refunds are processed within 5-7 business days and will be credited to your original payment method. UPI refunds are usually instant.', 'refunds', ARRAY['refund', 'time', 'how long', 'processing', 'days'], 8, true),
('What if my order is wrong or missing items?', 'We''re sorry for the inconvenience! Please contact us immediately with your order ID and we''ll either send the missing items or issue a full refund.', 'refunds', ARRAY['wrong', 'missing', 'incorrect', 'mistake'], 9, true),
('Can I get a refund if food quality is poor?', 'Absolutely! Your satisfaction is our priority. If the food quality doesn''t meet your expectations, contact us within 24 hours for a full refund.', 'refunds', ARRAY['refund', 'quality', 'poor', 'bad', 'cold'], 8, true),

-- Account FAQs
('How do I create an account?', 'Just start chatting with me! I''ll guide you through a quick phone verification to create your account. It takes less than 2 minutes.', 'account', ARRAY['account', 'register', 'sign up', 'create'], 9, true),
('I forgot my password. What should I do?', 'No worries! Just tell me "reset my password" and I''ll send you a verification code to your registered phone number to reset it.', 'account', ARRAY['password', 'forgot', 'reset', 'lost'], 8, true),
('How do I change my phone number?', 'You can update your phone number in your account settings. For security, we''ll send a verification code to both your old and new numbers.', 'account', ARRAY['phone', 'number', 'change', 'update', 'mobile'], 6, true),
('Can I delete my account?', 'Yes, you can request account deletion by contacting our support team. Please note this will delete all your order history and saved addresses.', 'account', ARRAY['delete', 'account', 'remove', 'close'], 5, true),

-- General FAQs
('Do you have dine-in or only delivery?', 'We offer all three options: delivery, takeaway, and dine-in at our restaurant. You can choose what works best for you!', 'general', ARRAY['dine in', 'takeaway', 'delivery', 'options'], 9, true),
('Are your ingredients fresh?', 'Absolutely! We source fresh ingredients daily from local suppliers and prepare everything in-house. Nothing frozen, nothing pre-packaged.', 'general', ARRAY['fresh', 'ingredients', 'quality', 'local'], 7, true),
('Do you cater to dietary restrictions?', 'Yes! We have vegetarian, vegan, and gluten-free options. Just tell me your dietary preferences and I''ll show you suitable items. You can also save your dietary restrictions in your profile.', 'general', ARRAY['dietary', 'vegan', 'vegetarian', 'gluten-free', 'allergens', 'restrictions'], 10, true),
('What are your restaurant hours?', 'We''re open from 11 AM to 11 PM every day. Kitchen closes at 10:30 PM for last orders.', 'general', ARRAY['hours', 'time', 'open', 'close', 'timing'], 8, true),
('Do you have parking available?', 'Yes! We have free parking for dine-in customers. The parking lot is right next to the restaurant entrance.', 'general', ARRAY['parking', 'car', 'vehicle'], 6, true),
('Do you offer catering for events?', 'Yes! We provide catering services for parties, corporate events, and weddings. Contact our catering team for custom menus and pricing.', 'general', ARRAY['catering', 'events', 'party', 'bulk', 'corporate'], 6, true),
('Are your dishes spicy?', 'We offer customizable spice levels: Mild, Medium, Spicy, and Extra Spicy. Just tell us your preference when ordering!', 'general', ARRAY['spicy', 'spice', 'level', 'mild', 'hot'], 7, true),
('Do you have a loyalty program?', 'Yes! Earn points with every order and redeem them for discounts. You automatically earn 1 point per Rs.10 spent.', 'general', ARRAY['loyalty', 'rewards', 'points', 'program'], 7, true),
('Can I book a table?', 'Yes! You can book a table through our chatbot. Just tell me your preferred date, time, and party size.', 'general', ARRAY['book', 'table', 'reservation', 'reserve'], 8, true),
('Do you deliver during bad weather?', 'We continue deliveries during light rain. However, we may suspend deliveries during severe weather conditions for our delivery partners'' safety.', 'general', ARRAY['weather', 'rain', 'storm'], 5, true);

-- Add restaurant-specific FAQs (if needed)
-- These would be populated from restaurant_config settings

-- Verify insertion
DO $$
DECLARE
    faq_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO faq_count FROM faq WHERE is_active = TRUE;
    RAISE NOTICE 'Successfully loaded % active FAQs', faq_count;
END $$;

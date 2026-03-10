const mongoose = require('mongoose');

const StoreSchema = new mongoose.Schema({
    name: { type: String, required: true },
    support_email: String,
    settings: {
        return_days_policy: { type: Number, default: 7 },
        allow_order_cancel: { type: Boolean, default: true },
        tone: { type: String, default: 'friendly' }
    }
});

const ProductSchema = new mongoose.Schema({
    name: { type: String, required: true },
    description: String,
    price: Number,
    stock: Number,
    store_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Store' }
});

const OrderSchema = new mongoose.Schema({
    customer_email: { type: String, required: true, index: true },
    status: { type: String, enum: ['processing', 'shipped', 'delivered', 'cancelled'], default: 'processing' },
    total_amount: Number,
    order_date: { type: Date, default: Date.now },
    delivery_date: Date,
    shipping_address: String,
    tracking_id: String,
    store_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Store' }
});

const ReturnSchema = new mongoose.Schema({
    order_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Order' },
    status: { type: String, enum: ['requested', 'approved', 'rejected', 'completed'], default: 'requested' },
    created_at: { type: Date, default: Date.now }
});

const TicketSchema = new mongoose.Schema({
    customer_email: { type: String, required: true },
    reason: String,
    status: { type: String, default: 'open' },
    created_at: { type: Date, default: Date.now }
});

module.exports = {
    Store: mongoose.model('Store', StoreSchema),
    Product: mongoose.model('Product', ProductSchema),
    Order: mongoose.model('Order', OrderSchema),
    Return: mongoose.model('Return', ReturnSchema),
    Ticket: mongoose.model('Ticket', TicketSchema)
};

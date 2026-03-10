const express = require('express');
const router = express.Router();
const { Order, Product, Return, Ticket, Store } = require('../models/Schemas');

// 1. Get Order Details
router.get('/orders/:id', async (req, res) => {
    try {
        const { email } = req.query;
        const order = await Order.findOne({
            $or: [{ _id: req.params.id }, { tracking_id: req.params.id }]
        }).populate('store_id');

        if (!order) return res.status(404).json({ error: 'Order not found' });
        if (order.customer_email.toLowerCase() !== email.toLowerCase()) {
            return res.status(401).json({ error: 'Email verification failed' });
        }

        res.json({
            status: 'success',
            order_id: order._id,
            status_label: order.status,
            order_date: order.order_date,
            delivery_date: order.delivery_date,
            total_amount: order.total_amount,
            shipping_address: order.shipping_address,
            tracking_id: order.tracking_id,
            store_name: order.store_id ? order.store_id.name : 'Main Store'
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 2. List Customer Orders
router.get('/orders', async (req, res) => {
    try {
        const { email } = req.query;
        const orders = await Order.find({ customer_email: email });
        res.json({ status: 'success', orders });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 3. Cancel Order
router.post('/orders/:id/cancel', async (req, res) => {
    try {
        const order = await Order.findById(req.params.id).populate('store_id');
        if (!order) return res.status(404).json({ error: 'Order not found' });

        const store = order.store_id;
        if (store && !store.settings.allow_order_cancel) {
            return res.status(400).json({ error: 'Cancellations disabled for this store' });
        }

        if (order.status !== 'processing') {
            return res.status(400).json({ error: `Cannot cancel order in ${order.status} status` });
        }

        order.status = 'cancelled';
        await order.save();
        res.json({ success: true, message: 'Order cancelled' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 4. Check Return Eligibility
router.get('/orders/:id/return-eligibility', async (req, res) => {
    try {
        const order = await Order.findById(req.params.id).populate('store_id');
        if (!order) return res.status(404).json({ eligible: false, reason: 'Order not found' });

        if (order.status !== 'delivered') {
            return res.json({ eligible: false, reason: 'Order must be delivered' });
        }

        const policyDays = order.store_id?.settings?.return_days_policy || 7;
        const deliveryDate = new Date(order.delivery_date);
        const today = new Date();
        const diffDays = Math.ceil((today - deliveryDate) / (1000 * 60 * 60 * 24));

        if (diffDays > policyDays) {
            return res.json({ eligible: false, reason: `Return window of ${policyDays} days expired` });
        }

        const existingReturn = await Return.findOne({ order_id: order._id });
        if (existingReturn) {
            return res.json({ eligible: false, reason: 'Return already requested' });
        }

        res.json({ eligible: true, policy_limit: policyDays });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 5. Get Product Info
router.get('/products/search', async (req, res) => {
    try {
        const { query } = req.query;
        const products = await Product.find({
            $or: [
                { name: { $regex: query, $options: 'i' } },
                { description: { $regex: query, $options: 'i' } }
            ]
        }).limit(5);
        res.json({ status: 'success', products });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 6. Create Support Ticket
router.post('/tickets', async (req, res) => {
    try {
        const { email, reason } = req.body;
        const ticket = new Ticket({ customer_email: email, reason });
        await ticket.save();
        res.json({ success: true, ticket_id: ticket._id });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;

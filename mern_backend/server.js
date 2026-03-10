require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const authMiddleware = require('./middleware/auth');
const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
// Apply API Key protection to all AI agent routes
app.use('/api/v1', authMiddleware, apiRoutes);

// Health Check
app.get('/health', (req, res) => res.json({ status: 'ok' }));
const aiRoutes = require('./routes/api');
const aiAuth = require('./middleware/auth');

// Protect these routes so only the AI Agent can call them
app.use('/api/v1/ai-connector', aiAuth, aiRoutes);

// Database Connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/ecommerce', {
    useNewUrlParser: true,
    useUnifiedTopology: true,
})
    .then(() => {
        console.log('Connected to MongoDB');
        app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
    })
    .catch(err => console.error('MongoDB connection error:', err));

require('dotenv').config();
const http = require('http');
const app = require('./app');
const connectDB = require('./config/db');
const socketIo = require('socket.io');
const logger = require('./config/logger');

const PORT = process.env.PORT || 5000;

connectDB().then(async () => {
    // Mock data seeding and live simulation disabled so we can show real predictions from dataset
});

const server = http.createServer(app);

const io = socketIo(server, {
    cors: {
        origin: '*',
    }
});

io.on('connection', (socket) => {
    logger.info(`New client connected: ${socket.id}`);
    socket.on('disconnect', () => {
        logger.info(`Client disconnected: ${socket.id}`);
    });
});

app.set('io', io);

server.listen(PORT, () => {
    logger.info(`Server running on port ${PORT}`);
});

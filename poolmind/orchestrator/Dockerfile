# Use official Node.js runtime as base image
FROM node:20.19-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install backend dependencies
RUN npm ci --only=production

# Copy frontend package files
COPY src/frontend/package*.json ./src/frontend/

# Install frontend dependencies
RUN cd src/frontend && npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build:all

# Remove frontend node_modules to reduce image size
RUN rm -rf src/frontend/node_modules

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Change ownership of app directory
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Start application
CMD ["npm", "start"] 
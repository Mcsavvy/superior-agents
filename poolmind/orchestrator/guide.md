# PoolMind Orchestrator API Development Instructions

## Project Overview

Build a Node.js REST API that serves as the central orchestrator for the PoolMind pooled crypto arbitrage fund platform. This API coordinates interactions between three main components:

- **Telegram Mini App** (user interface for deposits/withdrawals)
- **PoolMind Smart Contract** on Stacks blockchain (fund management)
- **AI Trading Agent** (arbitrage execution engine)

## Architecture Goals

The orchestrator acts as the single source of truth for:
- User account management and authentication
- Transaction coordination between Telegram app and smart contract
- NAV (Net Asset Value) updates from trading activities
- Capital management for AI agent trading operations
- Real-time pool status and analytics

## Technology Stack Requirements

### Core Framework
- **Backend**: Node.js with Express.js framework
- **Language**: TypeScript for type safety and better development experience
- **Database**: MongoDB with Mongoose ODM for flexible document storage
- **Blockchain**: Stacks SDK for JavaScript for smart contract interactions

### Supporting Technologies
- **Authentication**: JWT tokens with Telegram Web App authentication
- **Validation**: Request validation library (Zod or Joi)
- **Logging**: Structured logging system (Winston)
- **Documentation**: OpenAPI/Swagger for API documentation
- **Queue System**: Bull.js with Redis for background job processing
- **Environment Management**: dotenv for configuration

## Database Design (MongoDB Collections)

### Users Collection
Store Telegram user data, wallet addresses, KYC status, and account preferences. Each user document should track their telegram ID, linked Stacks wallet address, verification status, and account creation metadata.

### Deposits Collection
Track all user deposit transactions including STX amounts, PLMD shares received, NAV at time of deposit, transaction IDs, and status tracking through the deposit lifecycle.

### Withdrawals Collection
Record withdrawal requests with PLMD shares burned, STX amounts received, NAV at withdrawal time, transaction status, and processing timestamps.

### NavUpdates Collection
Maintain historical record of all NAV changes including old/new values, reasons for updates (trading profits/losses), transaction IDs, and timestamps for audit trail.

### TradingSessions Collection
Track AI agent trading activities including capital amounts deployed, session duration, profit/loss results, and emergency stop events.

### Transactions Collection
Universal transaction log for all blockchain interactions including deposits, withdrawals, NAV updates, and admin operations with full transaction details.

## API Endpoint Categories

### Authentication & User Management
Handle Telegram Web App authentication, user registration, wallet linking, KYC verification, and user profile management. Implement secure token-based authentication with proper session management.

### Pool Operations
Provide endpoints for user deposits and withdrawals, real-time pool status queries, balance inquiries, transaction history, and pool performance metrics.

### Smart Contract Integration
Create abstraction layer for all PoolMind contract interactions including deposit/withdraw calls, NAV updates, admin operations, and contract state queries.

### AI Agent Communication
Implement secure endpoints for AI agent to request trading capital, report trading results, update NAV based on trading performance, and handle emergency trading stops.

### Admin Operations
Provide platform administration endpoints for manual NAV adjustments, emergency pause controls, user management, and system configuration updates.

### Analytics & Reporting
Deliver comprehensive reporting including pool performance metrics, user analytics, trading session summaries, and financial reporting for compliance.

## Stacks Smart Contract Integration

### Contract Interaction Patterns
The orchestrator must seamlessly interact with the PoolMind Clarity smart contract functions:

**User Operations**: Handle deposit and withdrawal function calls, manage transaction broadcasting, monitor transaction confirmation, and update user balances accordingly.

**Admin Functions**: Execute NAV updates, manage admin STX deposits/withdrawals for trading, control pause states, and handle emergency operations.

**Read Operations**: Continuously query contract state for current NAV, total supply, individual balances, and contract configuration parameters.

### Transaction Management
Implement robust transaction handling with proper error recovery, retry mechanisms, transaction status monitoring, and user notification systems.

## Security Requirements

### Authentication Security
Implement Telegram Web App authentication validation, secure JWT token management, wallet signature verification for sensitive operations, and proper session handling.

### API Security
Add rate limiting, request validation, CORS configuration, input sanitization, and proper error handling without information leakage.

### Operational Security
Secure private key management for admin operations, multi-signature requirements for critical functions, audit logging for all operations, and proper environment variable handling.

### Data Protection
Implement data encryption for sensitive information, secure database connections, proper backup procedures, and compliance with data protection regulations.

## Integration Specifications

### Telegram Mini App Integration
Design API endpoints that seamlessly work with Telegram Web Apps including proper authentication flow, real-time balance updates, transaction status notifications, and user-friendly error messages.

### AI Agent Integration
Create secure communication channels for the AI trading agent including capital request workflows, profit/loss reporting, emergency stop mechanisms, and trading session management.

### Blockchain Integration
Implement reliable Stacks blockchain interaction including transaction broadcasting, confirmation monitoring, error handling, and state synchronization between off-chain database and on-chain contract.

## Background Processing Requirements

### Transaction Monitoring
Implement continuous monitoring of blockchain transactions for confirmation status, automatic retry of failed transactions, user notification systems, and database state updates.

### NAV Calculation
Create automated NAV calculation based on trading results, pool composition changes, fee calculations, and historical performance tracking.

### Notification System
Build comprehensive notification system for transaction confirmations, trading updates, system alerts, and performance reports through Telegram bot integration.

### Data Synchronization
Ensure consistent data synchronization between MongoDB database and Stacks smart contract state with conflict resolution and error recovery.

## Performance & Scalability

### Caching Strategy
Implement intelligent caching for frequently accessed data like current NAV, pool status, user balances, and contract state to reduce blockchain query load.

### Database Optimization
Design efficient MongoDB indexes, implement proper pagination for large datasets, optimize queries for real-time operations, and plan for horizontal scaling.

### API Performance
Add request/response compression, efficient pagination, proper HTTP caching headers, and connection pooling for database and blockchain interactions.

## Monitoring & Observability

### Application Monitoring
Implement comprehensive logging for all operations, error tracking and alerting, performance metrics collection, and health check endpoints.

### Business Metrics
Track key business metrics including total pool value, user growth, transaction volumes, trading performance, and system reliability.

### Operational Dashboards
Create monitoring dashboards for system health, transaction status, pool performance, and user activity with proper alerting mechanisms.

## Deployment Considerations

### Environment Configuration
Design for multiple environments (development, staging, production) with proper configuration management, secret handling, and environment-specific settings.

### Infrastructure Requirements
Plan for containerized deployment, load balancing, database clustering, Redis for caching/queues, and proper backup/recovery procedures.

### CI/CD Pipeline
Implement automated testing, code quality checks, security scanning, automated deployments, and proper rollback procedures.

## Compliance & Reporting

### Financial Compliance
Implement proper audit trails, transaction reporting, user verification workflows, and anti-money laundering (AML) compliance features.

### Regulatory Considerations
Design for potential regulatory requirements including user identification, transaction limits, geographical restrictions, and reporting obligations.

### Data Governance
Implement proper data retention policies, user data export capabilities, privacy controls, and compliance with data protection regulations.

## Development Guidelines

### Code Organization
Structure the application with clear separation of concerns, modular architecture, proper error handling, comprehensive testing, and maintainable documentation.

### API Design Principles
Follow RESTful design principles, implement consistent error responses, provide comprehensive API documentation, and ensure backward compatibility.

### Testing Strategy
Implement unit tests for business logic, integration tests for external services, end-to-end tests for critical workflows, and proper test data management.

### Documentation Requirements
Provide comprehensive API documentation, deployment guides, operational runbooks, and developer onboarding materials.

This orchestrator API serves as the critical infrastructure piece that enables secure, reliable, and scalable operation of the PoolMind platform while maintaining proper separation of concerns between user interface, blockchain, and AI trading components.
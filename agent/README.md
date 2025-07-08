# PoolMind Arbitrage Agent

This directory contains the PoolMind arbitrage agent implementation that extends the Superior Agents framework to execute automated STX arbitrage trades across multiple exchanges while maintaining integration with the PoolMind smart contract system.

## 🏗️ Architecture Overview

The PoolMind arbitrage agent consists of several key components:

### Core Components

1. **PoolMindArbitrageAgent** (`src/agent/poolmind_arbitrage.py`)
   - Main agent class that orchestrates the arbitrage workflow
   - Handles market analysis, strategy generation, and trade execution
   - Integrates with PoolMind API for fund management

2. **PoolMindSensor** (`src/sensor/poolmind.py`)
   - Monitors PoolMind pool state and exchange prices
   - Identifies arbitrage opportunities across supported exchanges
   - Provides real-time market data and risk assessment

3. **PoolMindClient** (`src/client/poolmind.py`)
   - Handles API interactions with PoolMind platform
   - Manages fund requests with HMAC authentication
   - Reports profits and updates NAV

4. **PoolMind Flow** (`src/flows/poolmind_arbitrage.py`)
   - Orchestrates the complete arbitrage trading workflow
   - Supports both single-cycle and continuous monitoring modes
   - Handles error recovery and graceful degradation

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Docker (for code execution containers)
- Access to PoolMind API
- Exchange API keys for supported exchanges

### Installation

1. **Clone the repository and navigate to the agent directory:**
   ```bash
   git clone <repository-url>
   cd superior-agents/agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp config/poolmind.env.example config/poolmind.env
   # Edit config/poolmind.env with your API keys and configuration
   ```

4. **Set up the database:**
   ```bash
   mkdir -p data logs
   ```

### Configuration

The agent requires several environment variables to be configured:

#### Required Configuration

- `POOLMIND_API_URL`: URL of the PoolMind API
- `POOLMIND_HMAC_SECRET`: HMAC secret for API authentication
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: LLM API keys
- Exchange API keys for supported exchanges

#### Optional Configuration

- `POOLMIND_MIN_PROFIT_THRESHOLD`: Minimum profit threshold (default: 0.5%)
- `POOLMIND_MAX_TRADE_SIZE_PERCENT`: Maximum trade size as % of pool (default: 10%)
- `POOLMIND_CONTINUOUS_MODE`: Enable continuous monitoring (default: false)

See `config/poolmind.env.example` for a complete configuration template.

### Running the Agent

#### Single Cycle Mode

Run a single arbitrage cycle:

```bash
python src/starter/poolmind_arbitrage_starter.py
```

#### Continuous Monitoring Mode

Enable continuous monitoring in your environment configuration:

```bash
export POOLMIND_CONTINUOUS_MODE=true
python src/starter/poolmind_arbitrage_starter.py
```

## 🔧 Supported Exchanges

The agent currently supports the following exchanges for STX arbitrage:

- **Binance**: Global cryptocurrency exchange
- **OKX**: Major cryptocurrency exchange
- **Gate.io**: Cryptocurrency exchange platform
- **Hotcoin**: Cryptocurrency trading platform
- **Bybit**: Derivatives and spot trading
- **CoinW**: Cryptocurrency exchange
- **OrangeX**: Cryptocurrency trading platform

### Adding New Exchanges

To add support for a new exchange:

1. **Update exchange configurations** in `src/starter/poolmind_arbitrage_starter.py`
2. **Implement exchange-specific price fetching** in `src/sensor/poolmind.py`
3. **Add exchange API credentials** to environment configuration
4. **Update supported exchanges list** in configuration

## 📊 Trading Workflow

The agent follows a structured workflow for each arbitrage opportunity:

### 1. Market Analysis
- Fetch real-time prices from all supported exchanges
- Analyze order book depth and liquidity
- Calculate potential arbitrage opportunities

### 2. Strategy Generation
- Generate trading strategy based on market analysis
- Assess risk factors and execution requirements
- Determine optimal trade sizes and timing

### 3. Risk Assessment
- Evaluate market volatility and execution risks
- Calculate risk scores and recommendations
- Apply risk management parameters

### 4. Fund Request
- Request funds from PoolMind based on opportunity size
- Include risk assessment and expected returns
- Wait for approval before proceeding

### 5. Trade Execution
- Execute simultaneous buy and sell orders
- Monitor execution progress and handle errors
- Calculate actual profits and fees

### 6. Profit Reporting
- Report trade results to PoolMind
- Update pool NAV based on profits
- Store strategy results for future reference

## 🔐 Security Features

### HMAC Authentication
- All API requests to PoolMind are authenticated with HMAC signatures
- Prevents unauthorized access and replay attacks
- Includes timestamp validation for request freshness

### Risk Management
- Configurable profit thresholds and trade size limits
- Automatic risk assessment for each opportunity
- Stop-loss mechanisms and position size controls

### Sandboxed Execution
- All generated code runs in isolated Docker containers
- Prevents system access and ensures security
- Timeout protection and resource limits

## 📈 Performance Monitoring

The agent tracks comprehensive performance metrics:

### Trading Metrics
- Total opportunities identified and executed
- Success rate and average profit per trade
- Risk-adjusted returns and Sharpe ratio
- Exchange-specific performance data

### Pool Impact Metrics
- NAV improvements from trading activities
- Percentage of pool actively traded
- Correlation with market conditions

### System Metrics
- Execution times and error rates
- API response times and availability
- Resource usage and system health

## 🛠️ Development

### Project Structure

```
agent/
├── src/
│   ├── agent/
│   │   └── poolmind_arbitrage.py     # Main agent implementation
│   ├── sensor/
│   │   └── poolmind.py               # Pool and market monitoring
│   ├── client/
│   │   └── poolmind.py               # PoolMind API client
│   ├── flows/
│   │   └── poolmind_arbitrage.py     # Trading workflow orchestration
│   ├── datatypes/
│   │   └── poolmind.py               # PoolMind-specific data types
│   └── starter/
│       └── poolmind_arbitrage_starter.py  # Agent startup script
├── config/
│   └── poolmind.env.example          # Configuration template
└── POOLMIND_ARBITRAGE_README.md      # This file
```

### Adding New Features

1. **New Trading Strategies**: Extend the `PoolMindArbitrageAgent` class
2. **Additional Sensors**: Implement new sensor classes following the existing pattern
3. **Enhanced Risk Management**: Modify risk assessment logic in the agent
4. **New Exchanges**: Add exchange-specific implementations

### Testing

Run tests for the PoolMind components:

```bash
# Run all tests
python -m pytest tests/

# Run specific component tests
python -m pytest tests/test_poolmind_agent.py
python -m pytest tests/test_poolmind_sensor.py
python -m pytest tests/test_poolmind_client.py
```

## 🚨 Troubleshooting

### Common Issues

1. **API Authentication Failures**
   - Check HMAC secret configuration
   - Verify system clock synchronization
   - Ensure API endpoint URLs are correct

2. **Exchange Connection Issues**
   - Verify exchange API keys and permissions
   - Check network connectivity and firewall settings
   - Review exchange-specific rate limits

3. **Container Execution Problems**
   - Ensure Docker is running and accessible
   - Check container image availability
   - Verify cache folder permissions

4. **Database Issues**
   - Check database file permissions
   - Ensure sufficient disk space
   - Verify database path configuration

### Logging

The agent provides comprehensive logging at multiple levels:

- **INFO**: General operation status and progress
- **DEBUG**: Detailed execution information
- **ERROR**: Error conditions and failures
- **WARNING**: Potential issues and fallbacks

Logs are written to both console and file (configurable via `POOLMIND_LOG_FILE`).

## 📚 API Reference

### PoolMindArbitrageAgent Methods

- `analyze_market()`: Perform market analysis across exchanges
- `generate_arbitrage_strategy()`: Create trading strategy
- `assess_risk()`: Evaluate opportunity risks
- `request_funds()`: Request funds from PoolMind
- `execute_arbitrage_trade()`: Execute trading strategy

### PoolMindSensor Methods

- `get_pool_state()`: Get current PoolMind pool status
- `get_exchange_prices()`: Fetch prices from all exchanges
- `identify_arbitrage_opportunities()`: Find profitable opportunities
- `get_market_metrics()`: Get comprehensive market data

### PoolMindClient Methods

- `request_funds()`: Request funds with HMAC authentication
- `report_profit()`: Report trading profits
- `update_nav()`: Update pool NAV
- `get_pool_state()`: Get pool status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Documentation

- [Superior Agents Architecture](../superior-agents.md)
- [PoolMind Platform Documentation](../poolmind.md)
- [Integration Guide](../Adapting%20Superior%20Agents%20for%20PoolMind%20.md)

## 📞 Support

For support and questions:

- Open an issue in the repository
- Contact the development team
- Check the troubleshooting section above

---

**Note**: This is a sophisticated trading system that handles real funds. Always test thoroughly in a development environment before deploying to production. Ensure you understand the risks associated with automated trading and have appropriate risk management measures in place. 
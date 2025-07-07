# PoolMind AI Agent

A modular AI engine for pooled cross-exchange arbitrage trading, leveraging collective intelligence for real-time arbitrage trading across fragmented crypto exchanges.

## Overview

The PoolMind AI Agent is a hybrid multi-agent system that optimizes returns for pooled capital while managing risk through LLM-powered decision-making. It integrates with the existing PoolMind ecosystem, which includes:

- Smart contracts (Clarity) for managing pooled funds
- Orchestrator backend (Node.js/Express) for authentication and API services
- Telegram bot interface for user interaction

## Architecture

The system follows a modular asynchronous workflow architecture with specialized components:

```
Market Sensors → Pool State Agent → Strategy Orchestrator → Risk Assessor → Action Validator → Trade Executor → Reflection Engine
```

### Core Components

1. **Exchange Adapter**: Direct integration with cryptocurrency exchange APIs
2. **Orchestrator Client**: Communication with external orchestration service
3. **Pool Context Engine**: Maintains real-time pool state
4. **Multi-LLM Strategy Generator**: Creates trading strategies based on pool state and market data
5. **Risk Assessment Module**: Evaluates opportunities against risk dimensions
6. **Execution Optimizer**: Handles gas-aware routing and slippage prediction
7. **Reflection & Learning Loop**: Analyzes outcomes and adjusts strategies

## Installation

### Prerequisites

- Python 3.9+
- Access to LLM APIs (OpenAI, Anthropic, etc.)
- Exchange API credentials

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/poolmind.git
cd poolmind/agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Environment Variables

The agent uses the following environment variables:

```
# Exchange API Credentials
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
GATE_API_KEY=your_gate_api_key
GATE_API_SECRET=your_gate_api_secret

# Orchestrator API
API_URL=https://api.orchestrator.example.com

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Mode Configuration
USE_MOCK_EXCHANGES=false  # Set to true for testing without real exchange API calls
USE_MOCK_API=false        # Set to true for testing without real orchestrator API calls
```

## Usage

### Running the Agent

```bash
# Run the agent directly
python -m poolmind_agent.main

# Run with specific configuration
python -m poolmind_agent.main --config config/production.yaml
```

### Running as a Standalone Process

The agent is designed to run as a standalone asynchronous process that communicates directly with exchange APIs and the orchestrator API.

```python
from poolmind_agent.core.agent import PoolMindAgent
from poolmind_agent.models.config import AgentConfig
import asyncio

async def main():
    # Load configuration
    config = AgentConfig.from_file("config/default.yaml")
    
    # Initialize agent
    agent = PoolMindAgent(config)
    await agent.initialize()
    
    # Run agent continuously
    await agent.run_continuous(interval_seconds=60)

if __name__ == "__main__":
    asyncio.run(main())
```

## Development

### Project Structure

```
agent/
├── src/
│   └── poolmind_agent/
│       ├── core/         # Core agent components and workflow
│       ├── models/       # Data models and schemas
│       ├── services/     # External service integrations
│       │   ├── exchange_adapter.py  # Exchange API integration
│       │   ├── exchange_client.py   # Exchange client facade
│       │   ├── orchestrator_client.py  # External API client
│       │   └── ...
│       └── utils/        # Helper utilities
├── tests/                # Test suite
│   ├── conftest.py       # Test fixtures
│   ├── mocks.py          # Mock implementations for testing
│   ├── test_agent.py     # Agent tests
│   └── test_services.py  # Service tests
├── config/               # Configuration files
├── pyproject.toml        # Project configuration
├── setup.py              # Package setup
└── README.md             # This file
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=poolmind_agent

# Run with mock mode (default)
USE_MOCK_EXCHANGES=true USE_MOCK_API=true pytest

# Run with real API mode (requires credentials)
USE_MOCK_EXCHANGES=false USE_MOCK_API=false pytest
```

## Performance Metrics

- Decision Latency: < 1.5s
- Opportunity Throughput: 50/min
- Prediction Accuracy: 85%
- Error Rate: < 0.5%
- Fallback Activation: < 5%

## Security & Compliance

The system implements:
- LLM output validation
- Encrypted API credentials via environment variables
- Rate limiting for exchange API calls
- Trade size ceilings
- Full decision provenance and audit trails

## License

MIT

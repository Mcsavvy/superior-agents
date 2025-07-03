# PoolMind AI Agent

A modular AI engine for pooled cross-exchange arbitrage trading, leveraging collective intelligence for real-time arbitrage trading across fragmented crypto exchanges.

## Overview

The PoolMind AI Agent is a hybrid multi-agent system that optimizes returns for pooled capital while managing risk through LLM-powered decision-making. It integrates with the existing PoolMind ecosystem, which includes:

- Smart contracts (Clarity) for managing pooled funds
- Orchestrator backend (Node.js/Express) for authentication and API services
- Telegram bot interface for user interaction

## Architecture

The system follows a modular architecture with specialized agents for discrete tasks:

```
Market Sensors → Pool State Agent → Strategy Orchestrator → Risk Assessor → Action Validator → Trade Executor → Reflection Engine
```

### Core Components

1. **Pool Context Engine**: Maintains real-time pool state
2. **Multi-LLM Strategy Generator**: Creates trading strategies based on pool state and market data
3. **Risk Assessment Module**: Evaluates opportunities against risk dimensions
4. **Execution Optimizer**: Handles gas-aware routing and slippage prediction
5. **Reflection & Learning Loop**: Analyzes outcomes and adjusts strategies

## Installation

### Prerequisites

- Python 3.9+
- Redis
- PostgreSQL
- Access to LLM APIs (OpenAI, Anthropic, etc.)

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

## Usage

### Starting the Agent

```python
from poolmind_agent import PoolMindAgent

agent = PoolMindAgent()
agent.start()
```

### API Integration

The agent exposes a FastAPI interface for integration with the existing PoolMind ecosystem:

```bash
# Start the API server
uvicorn poolmind_agent.api.main:app --reload
```

API documentation is available at `http://localhost:8000/docs` when the server is running.

## Development

### Project Structure

```
agent/
├── src/
│   └── poolmind_agent/
│       ├── api/          # FastAPI endpoints
│       ├── core/         # Core agent components
│       ├── models/       # Data models and schemas
│       ├── services/     # External service integrations
│       └── utils/        # Helper utilities
├── tests/                # Test suite
├── pyproject.toml        # Project configuration
├── setup.py              # Package setup
└── README.md             # This file
```

### Running Tests

```bash
pytest
pytest --cov=poolmind_agent  # With coverage
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
- Encrypted context storage
- Double-signature execution
- Trade size ceilings
- Full decision provenance and audit trails

## License

MIT

#!/usr/bin/env python3
"""
PoolMind Arbitrage Agent Setup Script

This script helps set up the PoolMind arbitrage agent by creating necessary
directories, checking dependencies, and providing configuration guidance.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 12):
        print("❌ Python 3.12 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True


def check_docker():
    """Check if Docker is available."""
    print("🐳 Checking Docker availability...")
    try:
        result = subprocess.run(
            ["docker", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Docker is available: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker is not available or not working")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker is not installed or not accessible")
        return False


def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    directories = [
        "data",
        "logs",
        "config",
        "cache"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created/verified directory: {directory}")


def create_config_file():
    """Create configuration file from template."""
    print("⚙️  Setting up configuration...")
    
    config_template = """# PoolMind Arbitrage Agent Configuration

# Agent Configuration
POOLMIND_AGENT_ID=poolmind-arbitrage-agent
POOLMIND_LOG_FILE=logs/poolmind_arbitrage.log

# LLM Configuration (at least one required)
POOLMIND_MODEL_BACKEND=deepseek_v3_or
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# PoolMind API Configuration (required)
POOLMIND_API_URL=http://localhost:3000
POOLMIND_HMAC_SECRET=your_poolmind_hmac_secret_here

# Trading Configuration
POOLMIND_SUPPORTED_EXCHANGES=binance,okx,gate,hotcoin,bybit,coinw,orangex
POOLMIND_MIN_PROFIT_THRESHOLD=0.5
POOLMIND_MAX_TRADE_SIZE_PERCENT=10.0
POOLMIND_STOP_LOSS_THRESHOLD=5.0

# Database Configuration
POOLMIND_DATABASE_PATH=data/poolmind_arbitrage.db

# RAG Configuration
RAG_API_URL=http://localhost:8080

# Container Configuration
CONTAINER_IMAGE=superioragents/agent-executor:latest
CONTAINER_CACHE_FOLDER=cache

# Monitoring Configuration
POOLMIND_MONITORING_INTERVAL=60
POOLMIND_CONTINUOUS_MODE=false

# Exchange API Keys (configure as needed)
# Binance
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# OKX
OKX_API_KEY=your_okx_api_key_here
OKX_API_SECRET=your_okx_api_secret_here
OKX_PASSPHRASE=your_okx_passphrase_here

# Gate.io
GATE_API_KEY=your_gate_api_key_here
GATE_API_SECRET=your_gate_api_secret_here

# Add other exchange keys as needed...
"""
    
    config_file = Path("config/poolmind.env")
    if not config_file.exists():
        config_file.write_text(config_template)
        print(f"✅ Created configuration file: {config_file}")
    else:
        print(f"⚠️  Configuration file already exists: {config_file}")
    
    print("\n📝 Next steps:")
    print("   1. Edit config/poolmind.env with your API keys")
    print("   2. Set POOLMIND_HMAC_SECRET for PoolMind API authentication")
    print("   3. Configure at least one LLM API key (OpenAI, Anthropic, or OpenRouter)")
    print("   4. Add exchange API keys for the exchanges you want to use")


def check_dependencies():
    """Check if required dependencies are available."""
    print("📦 Checking dependencies...")
    
    required_packages = [
        "docker",
        "requests",
        "loguru",
        "result",
        "anthropic",
        "openai"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📥 To install missing packages, run:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True


def pull_docker_image():
    """Pull the required Docker image."""
    print("🐳 Pulling Docker image...")
    try:
        result = subprocess.run(
            ["docker", "pull", "superioragents/agent-executor:latest"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        if result.returncode == 0:
            print("✅ Docker image pulled successfully")
            return True
        else:
            print(f"❌ Failed to pull Docker image: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Docker pull timed out")
        return False
    except Exception as e:
        print(f"❌ Error pulling Docker image: {e}")
        return False


def run_basic_test():
    """Run a basic test to verify setup."""
    print("🧪 Running basic setup test...")
    
    try:
        # Test importing the main components
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from src.agent.poolmind_arbitrage import PoolMindArbitragePromptGenerator
        from src.sensor.poolmind import PoolMindSensor
        from src.client.poolmind import PoolMindClient
        
        # Test basic initialization
        prompt_gen = PoolMindArbitragePromptGenerator()
        sensor = PoolMindSensor(
            poolmind_api_url="http://localhost:3000",
            supported_exchanges=["binance", "okx"],
            exchange_configs={"binance": {}, "okx": {}}
        )
        client = PoolMindClient(
            base_url="http://localhost:3000",
            agent_id="test-agent",
            hmac_secret="test-secret"
        )
        
        print("✅ Basic component initialization test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 PoolMind Arbitrage Agent Setup")
    print("=" * 50)
    
    success = True
    
    # Check prerequisites
    if not check_python_version():
        success = False
    
    if not check_docker():
        success = False
        print("   Docker is required for code execution containers")
    
    # Create directories
    create_directories()
    
    # Create configuration
    create_config_file()
    
    # Check dependencies
    if not check_dependencies():
        success = False
    
    # Pull Docker image if Docker is available
    if success:
        if not pull_docker_image():
            print("⚠️  Docker image pull failed, but you can try again later")
    
    # Run basic test
    if success:
        if not run_basic_test():
            success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        print("\n📖 Next steps:")
        print("   1. Configure your API keys in config/poolmind.env")
        print("   2. Start the PoolMind platform (orchestrator API)")
        print("   3. Start the RAG API service")
        print("   4. Run the agent:")
        print("      python src/starter/poolmind_arbitrage_starter.py")
        print("\n📚 Documentation:")
        print("   - See POOLMIND_ARBITRAGE_README.md for detailed instructions")
        print("   - Check the configuration file for all available options")
    else:
        print("❌ Setup encountered issues. Please resolve them before continuing.")
        print("   Check the error messages above for guidance.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
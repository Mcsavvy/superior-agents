#!/usr/bin/env python3
"""
PoolMind Agent Runner

This script provides a command-line interface to run the PoolMind agent.
"""
import os
import sys
import argparse
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.poolmind_agent.main import ArbitrageMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def run_agent(config_path: str = None, interval: int = 30):
    """
    Run the PoolMind agent
    
    Args:
        config_path: Path to config file
        interval: Check interval in seconds
    """
    try:
        # Create and initialize arbitrage monitor
        monitor = ArbitrageMonitor(config_path)
        
        # Set check interval
        monitor.check_interval = interval
        
        # Initialize
        await monitor.initialize()
        
        # Run in continuous mode
        await monitor.run_continuous()
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping agent")
    
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run the PoolMind agent")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    
    args = parser.parse_args()
    
    # Run the agent
    asyncio.run(run_agent(args.config, args.interval))

if __name__ == "__main__":
    main()

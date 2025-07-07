"""
FastAPI server for the PoolMind agent
"""
import logging
import os
import uvicorn
from typing import Optional

from poolmind_agent.api.endpoints import app
from poolmind_agent.utils.config import AgentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def run_server(host: str = "0.0.0.0", 
               port: int = 8000, 
               reload: bool = False,
               workers: int = 1,
               config_path: Optional[str] = None):
    """
    Run the FastAPI server
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Whether to reload on code changes
        workers: Number of worker processes
        config_path: Path to config file
    """
    # Set environment variables if config path provided
    if config_path:
        os.environ["POOLMIND_CONFIG_PATH"] = config_path
    
    # Log server start
    logger.info(f"Starting PoolMind Agent API server on {host}:{port}")
    
    # Run server
    uvicorn.run(
        "poolmind_agent.api.endpoints:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run PoolMind Agent API server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Reload on code changes")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--config", type=str, help="Path to config file")
    
    args = parser.parse_args()
    
    # Run server
    run_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        config_path=args.config,
    )

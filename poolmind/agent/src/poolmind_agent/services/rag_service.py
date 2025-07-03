"""
RAG Service - Interface for retrieval-augmented generation
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
import json
import os
from datetime import datetime

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from poolmind_agent.utils.config import AgentConfig

logger = logging.getLogger(__name__)

class RAGService:
    """
    Service for retrieval-augmented generation
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the RAG Service
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self._initialize_client()
        
        logger.info("RAG Service initialized")
    
    def _initialize_client(self) -> None:
        """
        Initialize ChromaDB client
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.config.rag_data_path, exist_ok=True)
            
            # Initialize client
            self.client = chromadb.PersistentClient(
                path=self.config.rag_data_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Initialize embedding function
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            
            # Initialize collections
            self._initialize_collections()
            
            logger.info(f"ChromaDB client initialized at {self.config.rag_data_path}")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {str(e)}")
            raise
    
    async def close(self) -> None:
        """
        Close the RAG service and any open resources
        """
        try:
            # ChromaDB doesn't have an explicit close method, but we can add cleanup here if needed
            logger.info("Closing RAG Service resources")
            return True
        except Exception as e:
            logger.error(f"Error closing RAG Service: {e}")
            return False
            
    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update the RAG service configuration
        
        Args:
            config_updates: Dictionary or AgentConfig with configuration updates
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Update local config reference
            self.config = config_updates
            
            # No need to re-initialize ChromaDB client as config changes typically
            # don't affect the client itself, but rather the RAG behavior
            
            logger.info("RAG Service configuration updated")
            return True
                
        except Exception as e:
            logger.error(f"Error updating RAG Service configuration: {str(e)}")
            return False
    
    def _initialize_collections(self) -> None:
        """
        Initialize ChromaDB collections
        """
        try:
            # Create collections if they don't exist
            self.strategy_collection = self.client.get_or_create_collection(
                name="strategies",
                embedding_function=self.embedding_function,
                metadata={"description": "Historical trading strategies"}
            )
            
            self.trade_collection = self.client.get_or_create_collection(
                name="trades",
                embedding_function=self.embedding_function,
                metadata={"description": "Historical trade outcomes"}
            )
            
            self.market_collection = self.client.get_or_create_collection(
                name="market_conditions",
                embedding_function=self.embedding_function,
                metadata={"description": "Historical market conditions"}
            )
            
            logger.info("ChromaDB collections initialized")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB collections: {str(e)}")
            raise
    
    async def retrieve_similar_strategies(self, 
                                        market_context: Dict[str, Any], 
                                        top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar historical strategies
        
        Args:
            market_context: Current market context
            top_k: Number of similar strategies to retrieve
            
        Returns:
            List of similar strategies
        """
        try:
            # Convert market context to query string
            query = self._market_context_to_query(market_context)
            
            # Query collection
            results = self.strategy_collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Parse results
            strategies = []
            
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    try:
                        # Parse document
                        strategy = json.loads(doc)
                        
                        # Add metadata
                        if results["metadatas"] and results["metadatas"][0]:
                            strategy["metadata"] = results["metadatas"][0][i]
                        
                        # Add distance
                        if results["distances"] and results["distances"][0]:
                            strategy["similarity"] = 1.0 - min(1.0, results["distances"][0][i])
                        
                        strategies.append(strategy)
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Error parsing strategy document: {doc}")
                        continue
            
            logger.info(f"Retrieved {len(strategies)} similar strategies")
            return strategies
            
        except Exception as e:
            logger.error(f"Error retrieving similar strategies: {str(e)}")
            return []
    
    async def retrieve_similar_market_conditions(self, 
                                               market_context: Dict[str, Any], 
                                               top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar historical market conditions
        
        Args:
            market_context: Current market context
            top_k: Number of similar market conditions to retrieve
            
        Returns:
            List of similar market conditions
        """
        try:
            # Convert market context to query string
            query = self._market_context_to_query(market_context)
            
            # Query collection
            results = self.market_collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Parse results
            conditions = []
            
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    try:
                        # Parse document
                        condition = json.loads(doc)
                        
                        # Add metadata
                        if results["metadatas"] and results["metadatas"][0]:
                            condition["metadata"] = results["metadatas"][0][i]
                        
                        # Add distance
                        if results["distances"] and results["distances"][0]:
                            condition["similarity"] = 1.0 - min(1.0, results["distances"][0][i])
                        
                        conditions.append(condition)
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Error parsing market condition document: {doc}")
                        continue
            
            logger.info(f"Retrieved {len(conditions)} similar market conditions")
            return conditions
            
        except Exception as e:
            logger.error(f"Error retrieving similar market conditions: {str(e)}")
            return []
    
    async def store_strategy(self, strategy: Dict[str, Any]) -> bool:
        """
        Store a strategy in the RAG database
        
        Args:
            strategy: Strategy to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate ID
            strategy_id = f"strategy-{datetime.now().timestamp()}"
            
            # Extract metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "pair": strategy.get("opportunity", {}).get("pair", ""),
                "buy_exchange": strategy.get("opportunity", {}).get("buy_exchange", ""),
                "sell_exchange": strategy.get("opportunity", {}).get("sell_exchange", ""),
                "profit_pct": strategy.get("opportunity", {}).get("estimated_profit_pct", 0)
            }
            
            # Convert strategy to string
            strategy_str = json.dumps(strategy)
            
            # Add to collection
            self.strategy_collection.add(
                ids=[strategy_id],
                documents=[strategy_str],
                metadatas=[metadata]
            )
            
            logger.info(f"Stored strategy with ID {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing strategy: {str(e)}")
            return False
    
    async def store_market_condition(self, condition: Dict[str, Any]) -> bool:
        """
        Store a market condition in the RAG database
        
        Args:
            condition: Market condition to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate ID
            condition_id = f"condition-{datetime.now().timestamp()}"
            
            # Extract metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "exchanges": ",".join(condition.get("exchanges", [])),
                "pairs": ",".join(condition.get("pairs", []))
            }
            
            # Convert condition to string
            condition_str = json.dumps(condition)
            
            # Add to collection
            self.market_collection.add(
                ids=[condition_id],
                documents=[condition_str],
                metadatas=[metadata]
            )
            
            logger.info(f"Stored market condition with ID {condition_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing market condition: {str(e)}")
            return False
    
    async def store_trade_outcome(self, outcome: Dict[str, Any]) -> bool:
        """
        Store a trade outcome in the RAG database
        
        Args:
            outcome: Trade outcome to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate ID
            outcome_id = f"trade-{datetime.now().timestamp()}"
            
            # Extract metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "pair": outcome.get("pair", ""),
                "profit": outcome.get("outcome", {}).get("profit", 0)
            }
            
            # Convert outcome to string
            outcome_str = json.dumps(outcome)
            
            # Add to collection
            self.trade_collection.add(
                ids=[outcome_id],
                documents=[outcome_str],
                metadatas=[metadata]
            )
            
            logger.info(f"Stored trade outcome with ID {outcome_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing trade outcome: {str(e)}")
            return False
    
    def _market_context_to_query(self, market_context: Dict[str, Any]) -> str:
        """
        Convert market context to query string
        
        Args:
            market_context: Market context
            
        Returns:
            Query string
        """
        # Extract key information
        pairs = market_context.get("pairs", [])
        exchanges = market_context.get("exchanges", [])
        
        # Build query
        query_parts = []
        
        if pairs:
            query_parts.append(f"Trading pairs: {', '.join(pairs)}")
        
        if exchanges:
            query_parts.append(f"Exchanges: {', '.join(exchanges)}")
        
        # Add market conditions if available
        if "market_conditions" in market_context:
            conditions = market_context["market_conditions"]
            
            if isinstance(conditions, dict):
                for key, value in conditions.items():
                    query_parts.append(f"{key}: {value}")
        
        # Add opportunity details if available
        if "opportunity" in market_context:
            opportunity = market_context["opportunity"]
            
            if isinstance(opportunity, dict):
                for key, value in opportunity.items():
                    query_parts.append(f"{key}: {value}")
        
        # Join parts
        query = ". ".join(query_parts)
        
        return query

"""
LLM Service - Interface for interacting with LLM providers
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
import json
import os
from datetime import datetime

from langchain_core.language_models.llms import BaseLLM
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks.manager import CallbackManager
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from poolmind_agent.utils.config import AgentConfig

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with LLM providers
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the LLM Service
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self._initialize_models()
        
        logger.info("LLM Service initialized")
    
    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update the LLM service configuration
        
        Args:
            config_updates: Dictionary or AgentConfig with configuration updates
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Update local config reference
            self.config = config_updates
            
            # Re-initialize models with new configuration
            self._initialize_models()
            
            logger.info("LLM Service configuration updated")
            return True
                
        except Exception as e:
            logger.error(f"Error updating LLM Service configuration: {str(e)}")
            return False
    
    def _initialize_models(self) -> None:
        """
        Initialize LLM models based on configuration
        """
        try:
            # Initialize primary model
            self.primary_model = self._create_model(
                model_name=self.config.primary_llm_model,
                temperature=self.config.primary_llm_temperature,
                streaming=self.config.enable_streaming
            )
            
            # Initialize fallback model if configured
            if self.config.fallback_llm_model:
                self.fallback_model = self._create_model(
                    model_name=self.config.fallback_llm_model,
                    temperature=self.config.fallback_llm_temperature,
                    streaming=self.config.enable_streaming
                )
            else:
                self.fallback_model = None
            
            # Initialize strategy model if configured
            if self.config.strategy_llm_model:
                self.strategy_model = self._create_model(
                    model_name=self.config.strategy_llm_model,
                    temperature=self.config.strategy_llm_temperature,
                    streaming=self.config.enable_streaming
                )
            else:
                self.strategy_model = self.primary_model
            
            logger.info(f"Initialized LLM models: primary={self.config.primary_llm_model}")
            
        except Exception as e:
            logger.error(f"Error initializing LLM models: {str(e)}")
            raise
    
    def _create_model(self, model_name: str, temperature: float, streaming: bool) -> BaseLLM:
        """
        Create an LLM model instance
        
        Args:
            model_name: Name of the model
            temperature: Temperature for generation
            streaming: Whether to enable streaming
            
        Returns:
            LLM model instance
        """
        callbacks = None
        if streaming:
            callbacks = CallbackManager([StreamingStdOutCallbackHandler()])
        
        # Get API key from environment
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
            
        # Use ChatOpenAI but with Groq API base and key
        return ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            streaming=streaming,
            callback_manager=callbacks if streaming else None,
            verbose=self.config.verbose_llm,
            openai_api_key=groq_api_key,  # Use Groq API key
            openai_api_base="https://api.groq.com/openai/v1"  # Groq API endpoint
        )
    
    async def generate_strategy(self, prompt: str) -> Optional[str]:
        """
        Generate a trading strategy using the strategy model
        
        Args:
            prompt: Prompt for strategy generation
            
        Returns:
            Generated strategy or None if generation failed
        """
        try:
            logger.debug("Generating trading strategy")
            
            # Use strategy model if available, otherwise use primary
            model = self.strategy_model or self.primary_model
            
            # Add system message for strategy generation
            messages = [
                SystemMessage(content=self.config.strategy_system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Generate strategy with timeout
            response = await asyncio.wait_for(
                self._generate_with_model(model, messages),
                timeout=self.config.strategy_timeout_seconds
            )
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Strategy generation timed out after {self.config.strategy_timeout_seconds}s")
            
            # Try fallback model if available
            if self.fallback_model:
                try:
                    logger.info("Attempting strategy generation with fallback model")
                    
                    messages = [
                        SystemMessage(content=self.config.strategy_system_prompt),
                        HumanMessage(content=prompt)
                    ]
                    
                    response = await asyncio.wait_for(
                        self._generate_with_model(self.fallback_model, messages),
                        timeout=self.config.fallback_timeout_seconds
                    )
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Fallback strategy generation failed: {str(e)}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating strategy: {str(e)}")
            
            # Try fallback model if available
            if self.fallback_model:
                try:
                    logger.info("Attempting strategy generation with fallback model")
                    
                    messages = [
                        SystemMessage(content=self.config.strategy_system_prompt),
                        HumanMessage(content=prompt)
                    ]
                    
                    response = await asyncio.wait_for(
                        self._generate_with_model(self.fallback_model, messages),
                        timeout=self.config.fallback_timeout_seconds
                    )
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Fallback strategy generation failed: {str(e)}")
                    return None
            
            return None
    
    async def assess_risk(self, prompt: str) -> Optional[str]:
        """
        Assess risk using the primary model
        
        Args:
            prompt: Prompt for risk assessment
            
        Returns:
            Risk assessment or None if assessment failed
        """
        try:
            logger.debug("Assessing risk")
            
            # Add system message for risk assessment
            messages = [
                SystemMessage(content=self.config.risk_system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Generate risk assessment with timeout
            response = await asyncio.wait_for(
                self._generate_with_model(self.primary_model, messages),
                timeout=self.config.risk_timeout_seconds
            )
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Risk assessment timed out after {self.config.risk_timeout_seconds}s")
            return None
            
        except Exception as e:
            logger.error(f"Error assessing risk: {str(e)}")
            return None
    
    async def generate_insights(self, prompt: str) -> Optional[str]:
        """
        Generate insights using the primary model
        
        Args:
            prompt: Prompt for insights generation
            
        Returns:
            Generated insights or None if generation failed
        """
        try:
            logger.debug("Generating insights")
            
            # Add system message for insights generation
            messages = [
                SystemMessage(content=self.config.reflection_system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Generate insights with timeout
            response = await asyncio.wait_for(
                self._generate_with_model(self.primary_model, messages),
                timeout=self.config.reflection_timeout_seconds
            )
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Insights generation timed out after {self.config.reflection_timeout_seconds}s")
            return None
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return None
    
    async def optimize_execution(self, prompt: str) -> Optional[str]:
        """
        Optimize execution using the primary model
        
        Args:
            prompt: Prompt for execution optimization
            
        Returns:
            Optimized execution plan or None if optimization failed
        """
        try:
            logger.debug("Optimizing execution")
            
            # Add system message for execution optimization
            messages = [
                SystemMessage(content=self.config.execution_system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Generate optimization with timeout
            response = await asyncio.wait_for(
                self._generate_with_model(self.primary_model, messages),
                timeout=self.config.execution_timeout_seconds
            )
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Execution optimization timed out after {self.config.execution_timeout_seconds}s")
            return None
            
        except Exception as e:
            logger.error(f"Error optimizing execution: {str(e)}")
            return None
    
    async def _generate_with_model(self, model: BaseLLM, messages: List[Any]) -> str:
        """
        Generate text with a model
        
        Args:
            model: LLM model
            messages: List of messages
            
        Returns:
            Generated text
        """
        try:
            # Generate text
            response = await model.agenerate([messages])
            
            # Extract generated text
            if response and response.generations and response.generations[0]:
                return response.generations[0][0].text
            
            return ""
            
        except Exception as e:
            logger.error(f"Error generating with model: {str(e)}")
            raise
    
    async def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON response from LLM
        
        Args:
            response: LLM response text
            
        Returns:
            Parsed JSON or None if parsing failed
        """
        try:
            # Extract JSON from response
            json_str = self._extract_json(response)
            
            if not json_str:
                logger.warning("No JSON found in response")
                return None
            
            # Parse JSON
            parsed = json.loads(json_str)
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Error processing JSON response: {str(e)}")
            return None
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text
        
        Args:
            text: Text containing JSON
            
        Returns:
            Extracted JSON string
        """
        # Look for JSON between triple backticks
        if "```json" in text and "```" in text.split("```json", 1)[1]:
            return text.split("```json", 1)[1].split("```", 1)[0].strip()
        
        # Look for JSON between double backticks
        if "``json" in text and "``" in text.split("``json", 1)[1]:
            return text.split("``json", 1)[1].split("``", 1)[0].strip()
        
        # Look for JSON between single backticks
        if "`json" in text and "`" in text.split("`json", 1)[1]:
            return text.split("`json", 1)[1].split("`", 1)[0].strip()
        
        # Look for JSON between triple backticks without language specifier
        if "```" in text and "```" in text.split("```", 1)[1]:
            json_str = text.split("```", 1)[1].split("```", 1)[0].strip()
            try:
                json.loads(json_str)
                return json_str
            except:
                pass
        
        # Look for JSON between curly braces
        if "{" in text and "}" in text:
            start = text.find("{")
            # Find the matching closing brace
            open_braces = 0
            for i in range(start, len(text)):
                if text[i] == "{":
                    open_braces += 1
                elif text[i] == "}":
                    open_braces -= 1
                    if open_braces == 0:
                        json_str = text[start:i+1]
                        try:
                            json.loads(json_str)
                            return json_str
                        except:
                            pass
        
        # If no JSON found, return empty string
        return ""

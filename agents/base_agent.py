from enum import Enum
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisState(Enum):
    OBSERVING = "observing"
    DECIDING = "deciding"
    ACTING = "acting"
    EVALUATING = "evaluating"
    CONCLUDED = "concluded"

class BaseAgent(ABC):
    def __init__(self, ticker: str, max_iterations: int = 5, confidence_threshold: float = 0.7):
        self.ticker = ticker
        self.state = AnalysisState.OBSERVING
        self.observations: Dict[str, Any] = {}
        self.decisions: List[Dict[str, Any]] = []
        self.actions_taken: List[Dict[str, Any]] = []
        self.confidence = 0.0
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        self.current_iteration = 0
        
    async def run(self) -> Dict[str, Any]:
        """Main agent execution loop"""
        logger.info(f"Starting analysis for {self.ticker}")
        
        while self.state != AnalysisState.CONCLUDED and self.current_iteration < self.max_iterations:
            logger.info(f"Iteration {self.current_iteration + 1}, State: {self.state.value}")
            
            if self.state == AnalysisState.OBSERVING:
                await self.observe()
            elif self.state == AnalysisState.DECIDING:
                await self.decide()
            elif self.state == AnalysisState.ACTING:
                await self.act()
            elif self.state == AnalysisState.EVALUATING:
                await self.evaluate()
                
            self.current_iteration += 1
            
        return self.conclude()
    
    @abstractmethod
    async def observe(self):
        """Gather initial data"""
        pass
    
    @abstractmethod
    async def decide(self):
        """Decide what needs investigation"""
        pass
    
    @abstractmethod
    async def act(self):
        """Execute investigations"""
        pass
    
    @abstractmethod
    async def evaluate(self):
        """Evaluate if we have enough information"""
        pass
    
    @abstractmethod
    def conclude(self) -> Dict[str, Any]:
        """Generate final analysis"""
        pass
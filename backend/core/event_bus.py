import asyncio
import logging
from typing import Callable, Dict, List, Any
from colorama import Fore, Style, init

# Initialize colorama for clean console output
init(autoreset=True)

class EventBus:
    """
    The central nervous system of Jarvis. 
    Modules (Voice, Planner, Tools) will publish and subscribe to events here 
    so nothing blocks the main thread.
    """
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger("JarvisEventBus")

    def subscribe(self, event_type: str, callback: Callable):
        """Register a function to run when a specific event occurs."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.info(f"{Fore.CYAN}Subscribed to event: {event_type}{Style.RESET_ALL}")

    async def publish(self, event_type: str, data: Any = None):
        """Emit an event to all registered subscribers."""
        self.logger.info(f"{Fore.GREEN}Event Emitted: {event_type} | Data: {data}{Style.RESET_ALL}")
        
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                # Run the callback asynchronously so it doesn't block the bus
                asyncio.create_task(callback(data))
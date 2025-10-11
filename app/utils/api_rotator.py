import time
from typing import List, Dict
from datetime import datetime, timedelta

class APIRotator:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
        self.usage_tracker: Dict[str, Dict] = {}
        self.setup_usage_tracker()
    
    def setup_usage_tracker(self):
        """Initialize usage tracker for all API keys"""
        for key in self.api_keys:
            self.usage_tracker[key] = {
                'last_used': None,
                'usage_count': 0,
                'error_count': 0,
                'last_error': None
            }
    
    def get_next_key(self) -> str:
        """Get the next available API key with rotation logic"""
        if not self.api_keys:
            raise ValueError("No API keys available")
        
        # Try to find a key that hasn't been used recently or has low usage
        for _ in range(len(self.api_keys)):
            key = self.api_keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            
            # Check if this key is suitable
            key_info = self.usage_tracker[key]
            
            # Skip if key had recent errors
            if (key_info['last_error'] and 
                (datetime.now() - key_info['last_error']).total_seconds() < 300):  # 5 minute cooldown
                continue
                
            # Update usage info
            key_info['last_used'] = datetime.now()
            key_info['usage_count'] += 1
            
            return key
        
        # If all keys have recent errors, return the one with oldest error
        oldest_error_key = min(
            self.api_keys,
            key=lambda k: self.usage_tracker[k]['last_error'] or datetime.min
        )
        return oldest_error_key
    
    def report_error(self, api_key: str, error: Exception):
        """Report an error for a specific API key"""
        if api_key in self.usage_tracker:
            self.usage_tracker[api_key]['error_count'] += 1
            self.usage_tracker[api_key]['last_error'] = datetime.now()
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        return {
            key: {
                'usage_count': info['usage_count'],
                'error_count': info['error_count'],
                'last_used': info['last_used'],
                'last_error': info['last_error']
            }
            for key, info in self.usage_tracker.items()
        }
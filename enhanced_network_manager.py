"""
Enhanced Network Manager with Retry Logic
Implements exponential backoff and comprehensive error handling for web platform
"""

import asyncio
import aiohttp
import time
import random
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    """Different retry strategies for different scenarios"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    IMMEDIATE = "immediate"

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retryable_status_codes: set = None
    retryable_exceptions: tuple = None
    
    def __post_init__(self):
        if self.retryable_status_codes is None:
            self.retryable_status_codes = {408, 429, 500, 502, 503, 504}
        if self.retryable_exceptions is None:
            self.retryable_exceptions = (
                aiohttp.ClientError,
                aiohttp.ServerDisconnectedError,
                aiohttp.ClientConnectorError,
                asyncio.TimeoutError,
                ConnectionError
            )

class NetworkManager:
    """Enhanced network manager with retry logic and performance monitoring"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_count': 0,
            'avg_response_time': 0.0,
            'error_distribution': {}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        text_data: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and performance monitoring
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            json_data: JSON payload
            text_data: Text payload
            retry_config: Custom retry configuration
            strategy: Retry strategy to use
            
        Returns:
            Response data with metadata
        """
        config = retry_config or self.config
        start_time = time.time()
        
        for attempt in range(config.max_attempts):
            try:
                # Make the request
                response_data = await self._single_request(
                    method, url, headers, json_data, text_data
                )
                
                # Update performance metrics
                response_time = time.time() - start_time
                self._update_metrics(success=True, response_time=response_time)
                
                return {
                    'success': True,
                    'data': response_data,
                    'status_code': response_data.get('status_code'),
                    'response_time': response_time,
                    'attempt': attempt + 1,
                    'total_time': time.time() - start_time
                }
                
            except Exception as e:
                # Check if we should retry
                if not self._should_retry(e, attempt, config):
                    self._update_metrics(success=False, error_type=type(e).__name__)
                    raise
                
                # Log retry attempt
                logger.warning(f"Request failed (attempt {attempt + 1}/{config.max_attempts}): {e}")
                
                # Calculate delay
                delay = self._calculate_delay(attempt, config, strategy)
                
                # Wait before retry
                if delay > 0:
                    await asyncio.sleep(delay)
                
                # Update retry count
                self.performance_metrics['retry_count'] += 1
        
        # All attempts failed
        self._update_metrics(success=False, error_type="MaxRetriesExceeded")
        raise Exception(f"Request failed after {config.max_attempts} attempts")
    
    async def _single_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]],
        json_data: Optional[Dict[str, Any]],
        text_data: Optional[str]
    ) -> Dict[str, Any]:
        """Make a single HTTP request"""
        if not self.session:
            raise RuntimeError("NetworkManager not initialized. Use async context manager.")
        
        request_headers = headers or {}
        request_headers.update({
            'User-Agent': 'AI-Model-Compare/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        async with self.session.request(
            method=method,
            url=url,
            headers=request_headers,
            json=json_data,
            data=text_data
        ) as response:
            
            # Check for HTTP errors
            if response.status >= 400:
                error_text = await response.text()
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=error_text
                )
            
            # Parse response
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                data = await response.json()
            else:
                data = await response.text()
            
            return {
                'status_code': response.status,
                'headers': dict(response.headers),
                'data': data,
                'content_type': content_type
            }
    
    def _should_retry(self, error: Exception, attempt: int, config: RetryConfig) -> bool:
        """Determine if request should be retried"""
        # Don't retry if we've reached max attempts
        if attempt >= config.max_attempts - 1:
            return False
        
        # Check for retryable exceptions
        if isinstance(error, config.retryable_exceptions):
            return True
        
        # Check for HTTP status codes
        if hasattr(error, 'status') and error.status in config.retryable_status_codes:
            return True
        
        return False
    
    def _calculate_delay(self, attempt: int, config: RetryConfig, strategy: RetryStrategy) -> float:
        """Calculate delay before next retry"""
        if strategy == RetryStrategy.IMMEDIATE:
            return 0
        elif strategy == RetryStrategy.FIXED_INTERVAL:
            delay = config.base_delay
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)
        else:  # EXPONENTIAL_BACKOFF
            delay = config.base_delay * (config.backoff_multiplier ** attempt)
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter to prevent thundering herd
        if config.jitter:
            jitter_amount = delay * 0.1 * random.random()
            delay += jitter_amount
        
        return delay
    
    def _update_metrics(self, success: bool, response_time: float = 0, error_type: str = None):
        """Update performance metrics"""
        self.performance_metrics['total_requests'] += 1
        
        if success:
            self.performance_metrics['successful_requests'] += 1
            # Update average response time
            total = self.performance_metrics['successful_requests']
            current_avg = self.performance_metrics['avg_response_time']
            new_avg = (current_avg * (total - 1) + response_time) / total
            self.performance_metrics['avg_response_time'] = new_avg
        else:
            self.performance_metrics['failed_requests'] += 1
            if error_type:
                self.performance_metrics['error_distribution'][error_type] = \
                    self.performance_metrics['error_distribution'].get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        total = self.performance_metrics['total_requests']
        if total == 0:
            return self.performance_metrics.copy()
        
        metrics = self.performance_metrics.copy()
        metrics['success_rate'] = self.performance_metrics['successful_requests'] / total
        metrics['failure_rate'] = self.performance_metrics['failed_requests'] / total
        metrics['retry_rate'] = self.performance_metrics['retry_count'] / total
        
        return metrics
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_count': 0,
            'avg_response_time': 0.0,
            'error_distribution': {}
        }

# Test the network manager
async def test_network_manager():
    """Run automatic tests for network manager"""
    print("🧪 Testing Network Manager...")
    
    test_results = []
    
    # Test 1: Basic request with retry logic
    try:
        async with NetworkManager() as manager:
            # This should work (testing with a reliable endpoint)
            result = await manager.make_request(
                'GET',
                'https://httpbin.org/get',
                {'test': 'value'}
            )
            
            success = result['success'] and result['status_code'] == 200
            test_results.append({
                'test': 'Basic Request with Retry',
                'passed': success,
                'details': f"Status: {result['status_code']}, Time: {result['response_time']:.2f}s"
            })
            
    except Exception as e:
        test_results.append({
            'test': 'Basic Request with Retry',
            'passed': False,
            'details': str(e)
        })
    
    # Test 2: Retry logic simulation (using invalid endpoint)
    try:
        retry_config = RetryConfig(max_attempts=2, base_delay=0.1)
        
        async with NetworkManager() as manager:
            try:
                await manager.make_request(
                    'GET',
                    'https://httpbin.org/status/500',
                    retry_config=retry_config
                )
                success = False
                details = "Should have failed with retry"
            except Exception as e:
                success = True
                details = f"Correctly failed after retries: {type(e).__name__}"
            
            test_results.append({
                'test': 'Retry Logic Simulation',
                'passed': success,
                'details': details
            })
            
    except Exception as e:
        test_results.append({
            'test': 'Retry Logic Simulation',
            'passed': False,
            'details': str(e)
        })
    
    # Test 3: Performance metrics
    try:
        async with NetworkManager() as manager:
            # Make multiple requests to generate metrics
            for _ in range(3):
                try:
                    await manager.make_request('GET', 'https://httpbin.org/get')
                except:
                    pass  # Ignore errors for metrics test
            
            metrics = manager.get_metrics()
            
            success = (
                metrics['total_requests'] >= 3 and
                'success_rate' in metrics and
                'avg_response_time' in metrics
            )
            
            test_results.append({
                'test': 'Performance Metrics',
                'passed': success,
                'details': f"Total: {metrics['total_requests']}, Success Rate: {metrics.get('success_rate', 0):.2f}"
            })
            
    except Exception as e:
        test_results.append({
            'test': 'Performance Metrics',
            'passed': False,
            'details': str(e)
        })
    
    # Print results
    passed = sum(1 for result in test_results if result['passed'])
    total = len(test_results)
    
    print(f"\n📊 Network Manager Test Results:")
    print(f"Passed: {passed}/{total}")
    
    for result in test_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if not result['passed']:
            print(f"   Details: {result['details']}")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(test_network_manager())

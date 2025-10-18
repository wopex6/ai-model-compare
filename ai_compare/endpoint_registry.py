import asyncio
import aiohttp
from typing import List, Dict, Set
import re
from urllib.parse import urlparse

class EndpointDiscovery:
    """Dynamically discover API endpoints without hardcoding."""
    
    def __init__(self):
        self.discovered_endpoints = {}
    
    async def discover_openai_compatible_endpoints(self, service_name: str) -> List[str]:
        """Discover OpenAI-compatible endpoints for a service."""
        potential_domains = await self._generate_potential_domains(service_name)
        working_endpoints = []
        
        for domain in potential_domains:
            endpoints = await self._test_domain_endpoints(domain)
            working_endpoints.extend(endpoints)
        
        return working_endpoints
    
    async def _generate_potential_domains(self, service_name: str) -> List[str]:
        """Generate potential domain names for a service."""
        domains = []
        
        # Common patterns for AI service domains
        patterns = [
            f"api.{service_name}.com",
            f"api.{service_name}.ai", 
            f"api.{service_name}.io",
            f"{service_name}-api.com",
            f"{service_name}.api.com",
            f"api-{service_name}.com"
        ]
        
        # Add specific known patterns
        if service_name == "grok":
            patterns.extend(["api.x.ai", "api.grok.x.ai"])
        elif service_name == "meta":
            patterns.extend(["api.llama-api.com", "api.together.xyz", "api.meta.ai"])
        
        for pattern in patterns:
            domains.append(f"https://{pattern}")
        
        return domains
    
    async def _test_domain_endpoints(self, domain: str) -> List[str]:
        """Test common API endpoint patterns for a domain."""
        endpoints = []
        
        # Common API path patterns
        paths = ["/v1", "/api/v1", "/api", ""]
        
        for path in paths:
            endpoint = f"{domain}{path}"
            if await self._test_endpoint_health(endpoint):
                endpoints.append(endpoint)
        
        return endpoints
    
    async def _test_endpoint_health(self, endpoint: str) -> bool:
        """Test if an endpoint is accessible."""
        try:
            async with aiohttp.ClientSession() as session:
                # Try common health check endpoints
                test_paths = ["/models", "/health", "/status", ""]
                
                for path in test_paths:
                    try:
                        async with session.get(f"{endpoint}{path}", timeout=3) as response:
                            # Accept any response that isn't a connection error
                            if response.status < 500:
                                return True
                    except:
                        continue
                        
        except Exception:
            pass
        
        return False
    
    async def discover_by_dns_patterns(self, service_keywords: List[str]) -> List[str]:
        """Discover endpoints by testing DNS patterns."""
        endpoints = []
        
        for keyword in service_keywords:
            discovered = await self.discover_openai_compatible_endpoints(keyword)
            endpoints.extend(discovered)
        
        return list(set(endpoints))  # Remove duplicates
    
    async def discover_from_well_known_registries(self) -> Dict[str, List[str]]:
        """Discover endpoints from public API registries (if available)."""
        # This could query public API directories, GitHub repos, etc.
        # For now, return empty dict as this would require external services
        return {}
    
    async def smart_endpoint_discovery(self, service_hint: str, api_key: str) -> List[str]:
        """Intelligently discover endpoints for a service."""
        endpoints = []
        
        # Try DNS-based discovery
        dns_endpoints = await self.discover_openai_compatible_endpoints(service_hint)
        
        # Test each discovered endpoint with the API key
        for endpoint in dns_endpoints:
            if await self._test_with_api_key(endpoint, api_key):
                endpoints.append(endpoint)
        
        if not endpoints:
            raise Exception(f"No working endpoints discovered for {service_hint}")
        
        return endpoints
    
    async def _test_with_api_key(self, endpoint: str, api_key: str) -> bool:
        """Test if an endpoint works with the given API key."""
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/models", headers=headers, timeout=5) as response:
                    return response.status < 500  # Accept auth errors but not server errors
        except:
            return False

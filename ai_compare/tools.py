"""
AI Tools and Function Calling System
Provides real-time data access for AI chatbots
"""

import requests
from typing import Dict, Optional, Any, List
from datetime import datetime
import json

class AITools:
    """Collection of tools that AI can use to fetch real-time data"""
    
    def __init__(self):
        self.available_tools = {
            "get_weather": self.get_weather,
            "get_current_time": self.get_current_time,
            "search_web": self.search_web
        }
    
    def get_tool_definitions(self) -> list:
        """Get tool definitions for function calling"""
        return [
            {
                "name": "get_weather",
                "description": "Get current weather information for a specific location. Returns temperature, conditions, humidity, and wind speed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location (e.g., 'Tokyo', 'New York', 'London')"
                        },
                        "units": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature units (default: celsius)"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_current_time",
                "description": "Get the current date and time. If no timezone is specified, automatically detects the user's timezone from their location/IP. You can also specify a timezone for other locations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Optional timezone (e.g., 'America/New_York', 'Asia/Tokyo'). Leave empty or use 'auto' to detect user's timezone automatically."
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "search_web",
                "description": "Search for current information on the web. Use this for recent events, news, or facts that may have changed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    
    def get_weather(self, location: str, units: str = "celsius") -> Dict[str, Any]:
        """
        Get current weather for a location using OpenWeatherMap API
        
        Free API: https://openweathermap.org/api
        Sign up for free API key at: https://openweathermap.org/appid
        """
        try:
            # Using wttr.in - a free weather API that doesn't require API key
            # Format: wttr.in/location?format=j1
            url = f"https://wttr.in/{location}?format=j1"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            current = data['current_condition'][0]
            
            temp_c = current['temp_C']
            temp_f = current['temp_F']
            
            return {
                "location": location,
                "temperature": f"{temp_c}°C ({temp_f}°F)" if units == "celsius" else f"{temp_f}°F ({temp_c}°C)",
                "temperature_celsius": temp_c,
                "temperature_fahrenheit": temp_f,
                "condition": current['weatherDesc'][0]['value'],
                "feels_like": f"{current['FeelsLikeC']}°C" if units == "celsius" else f"{current['FeelsLikeF']}°F",
                "humidity": f"{current['humidity']}%",
                "wind_speed": f"{current['windspeedKmph']} km/h",
                "visibility": f"{current['visibility']} km",
                "pressure": f"{current['pressure']} mb",
                "observation_time": current['observation_time']
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to fetch weather data: {str(e)}",
                "location": location
            }
        except (KeyError, IndexError) as e:
            return {
                "error": f"Failed to parse weather data: {str(e)}",
                "location": location
            }
    
    def get_current_time(self, timezone: str = None) -> Dict[str, Any]:
        """Get current time for a timezone or auto-detect from IP"""
        try:
            # Using worldtimeapi.org - free API, no key required
            if timezone and timezone != "auto":
                # Use specified timezone
                url = f"http://worldtimeapi.org/api/timezone/{timezone}"
            else:
                # Auto-detect timezone from user's IP
                url = "http://worldtimeapi.org/api/ip"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "timezone": data.get('timezone', 'UTC'),
                "datetime": data.get('datetime', ''),
                "date": data.get('datetime', '')[:10],
                "time": data.get('datetime', '')[11:19],
                "day_of_week": data.get('day_of_week', ''),
                "day_of_year": data.get('day_of_year', ''),
                "utc_offset": data.get('utc_offset', ''),
                "detected": timezone is None or timezone == "auto"
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to fetch time data: {str(e)}",
                "datetime": datetime.now().isoformat(),
                "note": "Using server time as fallback",
                "timezone": "UTC"
            }
    
    def search_web(self, query: str) -> Dict[str, Any]:
        """
        Simulated web search - returns a message
        For real implementation, integrate with:
        - DuckDuckGo API (free)
        - Google Custom Search API
        - Bing Search API
        """
        return {
            "query": query,
            "message": "Web search functionality requires API integration. Currently returning simulated results.",
            "note": "To enable: Add DuckDuckGo API or Google Custom Search API key",
            "suggestion": f"I don't have direct web search access, but I can help you search for '{query}' if you provide me with specific information or context."
        }
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        if tool_name not in self.available_tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        try:
            tool_function = self.available_tools[tool_name]
            result = tool_function(**parameters)
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}


class FunctionCallingParser:
    """Parse and handle function calling from AI responses"""
    
    @staticmethod
    def should_use_tools(message: str) -> bool:
        """Detect if user query needs real-time data"""
        real_time_indicators = [
            "current", "now", "today", "right now", "at the moment",
            "latest", "recent", "what is the", "what's the",
            "temperature", "weather", "time", "date",
            "stock price", "news", "happening"
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in real_time_indicators)
    
    @staticmethod
    def extract_location(message: str) -> Optional[str]:
        """Extract location from weather-related queries"""
        import re
        
        # Patterns to detect location
        patterns = [
            r"in ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # "in Tokyo"
            r"at ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # "at New York"
            r"for ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", # "for London"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s",   # "Tokyo's weather"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def extract_multiple_locations(message: str) -> List[str]:
        """Extract multiple locations/cities from query"""
        import re
        
        # Common patterns for multiple locations
        message_lower = message.lower()
        locations = []
        
        # City/timezone mapping for common cities
        city_mappings = {
            "melbourne": "Australia/Melbourne",
            "sydney": "Australia/Sydney", 
            "perth": "Australia/Perth",
            "brisbane": "Australia/Brisbane",
            "ukraine": "Europe/Kiev",
            "kiev": "Europe/Kiev",
            "kyiv": "Europe/Kiev",
            "new york": "America/New_York",
            "tokyo": "Asia/Tokyo",
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "singapore": "Asia/Singapore",
            "hong kong": "Asia/Hong_Kong",
            "los angeles": "America/Los_Angeles",
            "chicago": "America/Chicago"
        }
        
        # Find all mentioned cities
        for city, timezone in city_mappings.items():
            if city in message_lower:
                locations.append((city, timezone))
        
        return locations
    
    @staticmethod
    def enhance_prompt_with_tools(message: str, tools: AITools, use_ai_fallback: bool = True) -> tuple[str, Optional[Dict]]:
        """
        Enhance user message with tool results if needed
        Returns: (enhanced_message, tool_results)
        
        Strategy:
        1. Try custom tools (weather API, time API) - Fast & Free
        2. If tools fail and use_ai_fallback=True, let AI platforms handle it
        3. AI platforms with real-time access: GPT-4, Gemini, Grok
        """
        if not FunctionCallingParser.should_use_tools(message):
            return message, None
        
        tool_results = {}
        tool_success = False
        
        # Check for weather queries
        if any(word in message.lower() for word in ["weather", "temperature", "hot", "cold", "rain"]):
            location = FunctionCallingParser.extract_location(message)
            if location:
                weather_data = tools.get_weather(location)
                tool_results['weather'] = weather_data
                
                # Add weather data to message if successful
                if 'error' not in weather_data:
                    enhanced_message = f"{message}\n\n[REAL-TIME DATA: Current weather in {location}: {weather_data['temperature']}, {weather_data['condition']}, Humidity: {weather_data['humidity']}, Wind: {weather_data['wind_speed']}]"
                    tool_success = True
                    return enhanced_message, tool_results
                else:
                    # Tool failed - add instruction for AI fallback
                    if use_ai_fallback:
                        enhanced_message = f"{message}\n\n[INSTRUCTION: Weather API failed. If you have access to real-time web search (GPT-4 browsing, Gemini search, etc.), please fetch current weather for {location}. Otherwise, acknowledge that you cannot access real-time data.]"
                        tool_results['fallback_mode'] = 'ai_search'
                        return enhanced_message, tool_results
        
        # Check for time queries - HANDLE MULTIPLE LOCATIONS
        if any(word in message.lower() for word in ["time", "date", "today", "now"]):
            # Extract multiple locations
            locations = FunctionCallingParser.extract_multiple_locations(message)
            
            if locations and len(locations) > 0:
                # Fetch time for each location
                time_data_list = []
                for city, timezone in locations:
                    time_data = tools.get_current_time(timezone)
                    if 'error' not in time_data:
                        time_data_list.append({
                            'city': city.title(),
                            'timezone': timezone,
                            'time': time_data['time'],
                            'date': time_data['date'],
                            'full_datetime': time_data['datetime'],
                            'utc_offset': time_data['utc_offset']
                        })
                
                if time_data_list:
                    # Build enhanced message with all times
                    real_time_data = "[REAL-TIME DATA - CURRENT TIMES:\n"
                    for data in time_data_list:
                        real_time_data += f"• {data['city']}: {data['time']} ({data['date']}) - {data['timezone']} (UTC{data['utc_offset']})\n"
                    real_time_data += "]\n\n[INSTRUCTION: Use ONLY the times provided above. DO NOT answer from memory. Present these times clearly to the user.]"
                    
                    enhanced_message = f"{message}\n\n{real_time_data}"
                    tool_results['times'] = time_data_list
                    tool_success = True
                    return enhanced_message, tool_results
            else:
                # Single location or auto-detect
                time_data = tools.get_current_time()
                tool_results['time'] = time_data
                
                if 'error' not in time_data:
                    enhanced_message = f"{message}\n\n[REAL-TIME DATA: Current time: {time_data['time']} ({time_data['date']}) - {time_data['timezone']}]\n\n[INSTRUCTION: Use ONLY the time provided above. DO NOT answer from memory.]"
                    tool_success = True
                    return enhanced_message, tool_results
                else:
                    # Tool failed - add instruction for AI fallback
                    if use_ai_fallback:
                        enhanced_message = f"{message}\n\n[INSTRUCTION: Time API failed. If you have access to real-time data, please provide the current date/time. Otherwise, acknowledge that you cannot access real-time data.]"
                        tool_results['fallback_mode'] = 'ai_search'
                        return enhanced_message, tool_results
        
        # General real-time queries (news, stocks, etc.)
        real_time_keywords = ["latest", "current", "recent", "today's", "breaking", "stock price", "news about"]
        if any(keyword in message.lower() for keyword in real_time_keywords):
            if use_ai_fallback:
                enhanced_message = f"{message}\n\n[INSTRUCTION: This query requires real-time data. If you have web search capability (GPT-4 browsing, Gemini search, Grok), please search and provide current information. Otherwise, acknowledge your knowledge cutoff date.]"
                tool_results['fallback_mode'] = 'ai_search'
                tool_results['query_type'] = 'general_realtime'
                return enhanced_message, tool_results
        
        return message, tool_results

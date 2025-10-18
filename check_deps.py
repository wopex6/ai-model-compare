import sys
print(f"Python version: {sys.version}")

try:
    import openai
    print(f"OpenAI version: {openai.__version__}")
except ImportError:
    print("OpenAI not installed")

try:
    from dotenv import load_dotenv
    print("python-dotenv available")
except ImportError:
    print("python-dotenv not installed")

try:
    import aiohttp
    print("aiohttp available")  
except ImportError:
    print("aiohttp not installed")

print("Dependencies check complete")

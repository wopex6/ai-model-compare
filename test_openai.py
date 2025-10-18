import asyncio
from ai_compare.simple_models import ChatGPTModel

async def test():
    try:
        model = ChatGPTModel()
        response = await model.get_response("What is AI?")
        print("SUCCESS:", response)
    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

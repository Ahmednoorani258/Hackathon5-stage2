from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, RunConfig
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# OPENROUTER_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("9ROUTERKEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

external_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    # base_url="https://openrouter.ai/api/v1",
    base_url="https://rfvgyxs.9router.com/v1",
    # base_url="https://generativelanguage.googleapis.com/v1beta",
)

model = OpenAIChatCompletionsModel(
    # model="nvidia/nemotron-3-super-120b-a12b:free",
    model="myfreecombo-oauth",
    # model="gemini-2.0-flash",
    openai_client=external_client,
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True,
)
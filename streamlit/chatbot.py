import config
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from prompts import SYSTEM_MESSAGE, AUGMENTED_PROMPT


class ChatBot:
    def __init__(self, vectorstore, openai_api_key):
        self.vectorstore = vectorstore
        provider = OpenAIProvider(api_key=openai_api_key)
        model = OpenAIChatModel(config.LLM_MODEL, provider=provider)
        self.agent = Agent(
            model,
            instructions=SYSTEM_MESSAGE["content"],
        )

    def augment_prompt(self, query: str) -> str:
        context = self.vectorstore.similarity_search(query, k=3)
        context = "\n".join([doc.page_content for doc in context])
        print("AUGMENTED PROMPT:", AUGMENTED_PROMPT.format(query=query, context=context))
        return AUGMENTED_PROMPT.format(query=query, context=context)

    def chat(self, query: str) -> str:
        augmented_query = self.augment_prompt(query)
        augmented_response = self.agent.run_sync(augmented_query)
        return augmented_response.output

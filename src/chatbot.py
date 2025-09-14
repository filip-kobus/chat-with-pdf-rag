import config
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from prompts import SYSTEM_PROMPT, AUGMENTED_PROMPT


class ChatBot:
    def __init__(self, vectorstore, openai_api_key, session_id):
        self.vectorstore = vectorstore
        self.session_id = session_id
        provider = OpenAIProvider(api_key=openai_api_key)
        model = OpenAIChatModel(config.LLM_MODEL, provider=provider)
        self.agent = Agent(
            model,
            instructions=SYSTEM_PROMPT,
        )

    def augment_prompt(self, query: str) -> str:
        context = self.vectorstore.similarity_search(
            query, 
            k=3, 
            filter={"session_id": self.session_id}
        )

        if not context:
            return query
        
        context = "\n".join([doc.page_content for doc in context])
        return AUGMENTED_PROMPT.format(query=query, context=context)

    def chat(self, query: str) -> str:
        augmented_query = self.augment_prompt(query)
        augmented_response = self.agent.run_sync(augmented_query)
        return augmented_response.output

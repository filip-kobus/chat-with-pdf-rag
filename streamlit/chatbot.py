import config
from pydantic_ai import Agent
from prompts import SYSTEM_MESSAGE, AUGMENTED_PROMPT


class ChatBot:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.agent = Agent(
            config.LLM_MODEL,
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

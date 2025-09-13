SYSTEM_MESSAGE = {
    "role": "system",
    "content": """If the context does not provide enough information, answer based on your knowledge.
                    If the context is not relevant, don't mention it, just answer question.
                    Answer in one, if necessary, two sentences. Be concise and clear.""",
}

AUGMENTED_PROMPT = """Answer the following question using the context provided below.

Question: {query}
Context: {context}"""

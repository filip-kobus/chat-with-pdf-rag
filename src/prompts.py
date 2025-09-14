SYSTEM_PROMPT = (
    "If the context does not provide enough information, answer based on your knowledge."
    "If the context is not relevant, don't mention it, just answer question."
    "Give short and concise answers."
    "Always answer in the language of the question."
)

AUGMENTED_PROMPT = (
    "Answer the following question using the context provided below."
    "\n\nContext:\n{context}\n\nQuestion: {query}\n\n"
)

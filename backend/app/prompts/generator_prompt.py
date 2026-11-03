"""Prompts for Node 4: the answer generator."""

BASE_SYSTEM_PROMPT = """You are a precise, helpful research assistant inside a RAG application.
Always answer in the same language the user wrote their question in.
Use clean Markdown (short paragraphs, lists, tables or code blocks only when they help)."""

PDF_CONTEXT_INSTRUCTIONS = """Answer using ONLY the numbered context below, which comes from the user's uploaded documents.
- Cite the sources you rely on inline as [1], [2] matching the numbers in the context.
- If the context does not contain the answer, say so plainly instead of guessing.
- Never invent page numbers, quotes or figures."""

WEB_CONTEXT_INSTRUCTIONS = """Answer using the numbered web search results below. They are current as of today.
- Cite the sources you rely on inline as [1], [2] matching the numbers in the context.
- If results conflict, say so and prefer the most recent / most authoritative source.
- If the results do not answer the question, say so plainly instead of guessing."""

MIXED_INSTRUCTIONS = """The numbered context mixes uploaded-document passages and web results.
Cite with [n] and make clear which facts come from the documents and which from the web."""

DIRECT_INSTRUCTIONS = """No external context is needed for this message. Answer directly and concisely.
If you are not sure about a fact, say so."""

NO_CONTEXT_INSTRUCTIONS = """A search was attempted but returned nothing usable.
Tell the user you could not find reliable information, and suggest how to rephrase or what to upload.
Do not invent facts."""

FALLBACK_NOTE = (
    "Note: the uploaded documents did not contain relevant information, so the system "
    "searched the web instead. Mention this briefly at the start of your answer."
)

CONTEXT_TEMPLATE = """### Context
{context}"""


def build_system_prompt(
    *,
    has_pdf_context: bool,
    has_web_context: bool,
    retrieval_attempted: bool,
    used_fallback: bool,
    context_block: str,
) -> str:
    parts = [BASE_SYSTEM_PROMPT]
    if has_pdf_context and has_web_context:
        parts.append(MIXED_INSTRUCTIONS)
    elif has_pdf_context:
        parts.append(PDF_CONTEXT_INSTRUCTIONS)
    elif has_web_context:
        parts.append(WEB_CONTEXT_INSTRUCTIONS)
        if used_fallback:
            parts.append(FALLBACK_NOTE)
    elif retrieval_attempted:
        parts.append(NO_CONTEXT_INSTRUCTIONS)
    else:
        parts.append(DIRECT_INSTRUCTIONS)

    if context_block:
        parts.append(CONTEXT_TEMPLATE.format(context=context_block))
    return "\n\n".join(parts)

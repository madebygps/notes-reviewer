"""Service for LLM-based summarization using Ollama."""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from ollama import Client

from config import Config, get_config

logger = logging.getLogger(__name__)


class LLMService:
    """Handles LLM operations for summarization and analysis."""

    def __init__(self, config: Config) -> None:
        """Initialize the LLM service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.client = Client(host=config.ollama_base_url)
        self.model = config.ollama_llm_model

    async def summarize_search_results(
        self,
        query: str,
        results: list[dict],
    ) -> str:
        """Generate a summary of search results using LLM.

        Args:
            query: Original search query
            results: List of search result dictionaries with 'text' and 'metadata'

        Returns:
            AI-generated summary of the findings

        Raises:
            ValueError: If response format is unexpected
            RuntimeError: If summarization fails
        """
        try:
            if not results:
                logger.debug("No results to summarize")
                return "No results found to summarize."

            logger.info(f"Generating summary for query: '{query}' with {len(results)} results")

            # Prepare context from results
            context_parts = []
            for i, result in enumerate(results, 1):
                text = result.get("text", "")
                metadata = result.get("metadata", {})
                source = metadata.get("filename", metadata.get("source_type", "Unknown"))
                
                # Truncate long texts
                text_preview = text[:500] + "..." if len(text) > 500 else text
                context_parts.append(
                    f"Document {i} (Source: {source}):\n{text_preview}"
                )

            context = "\n\n".join(context_parts)

            # Create prompt for summarization
            prompt = f"""You are analyzing search results from a notes database. The user searched for: "{query}"

Here are the top {len(results)} most relevant documents found:

{context}

Please provide a concise summary of the key findings across these documents. Focus on:
1. Main themes and topics found
2. Important information related to the query
3. Any patterns or connections between the documents

Keep your summary clear, informative, and under 200 words."""

            # Generate summary using LLM (run in thread pool to avoid blocking)
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                options={
                    "temperature": 0.7,
                    "num_predict": 300,
                },
            )

            # Extract the summary text
            if hasattr(response, "message"):
                return response.message.content
            elif isinstance(response, dict) and "message" in response:
                return response["message"]["content"]
            else:
                raise ValueError(f"Unexpected response format: {type(response)}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            raise RuntimeError(f"Failed to generate summary: {str(e)}") from e


@lru_cache
def get_llm_service() -> LLMService:
    """Get cached LLM service instance.

    Returns:
        LLMService instance
    """
    config = get_config()
    return LLMService(config)

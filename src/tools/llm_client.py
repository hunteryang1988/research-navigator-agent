"""
LLM client wrapper for OpenAI API calls.

Provides unified interface for reasoning and synthesis with GPT models.
"""

from typing import Optional, Dict, Any
from openai import OpenAI
from rich.console import Console

from src.config.settings import get_settings
from src.tools.api_logger import (
    APICallLogger,
    log_llm_call,
    log_llm_response,
)

console = Console()


class LLMClient:
    """
    Wrapper for OpenAI LLM API calls with logging and error handling.
    """

    def __init__(self):
        """Initialize LLM client with settings."""
        self.settings = get_settings()

        # Initialize OpenAI client
        client_kwargs = {
            "api_key": self.settings.openai_api_key,
        }

        # Add custom base URL if configured
        if self.settings.openai_base_url:
            client_kwargs["base_url"] = self.settings.openai_base_url

        self.client = OpenAI(**client_kwargs)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[list] = None,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generate text using the configured LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature (uses config default if None)
            max_tokens: Max tokens (uses config default if None)
            stop_sequences: Optional stop sequences

        Returns:
            Tuple of (response_text, metadata_dict)
            metadata includes: prompt_tokens, completion_tokens, total_tokens, model

        Raises:
            Exception: If API call fails
        """
        # Use defaults from settings if not provided
        if temperature is None:
            temperature = self.settings.llm_temperature
        if max_tokens is None:
            max_tokens = self.settings.llm_max_tokens

        # Log LLM call details
        log_llm_call(
            model=self.settings.llm_model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            prompt_length=len(prompt),
        )

        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Make API call with tracking
        with APICallLogger(
            api_name="OpenAI Chat",
            operation="LLM text generation",
            model=self.settings.llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
        ) as logger:
            response = self.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,  # Use max_completion_tokens instead of max_tokens for newer models
                stop=stop_sequences,
            )

            # Extract response
            response_text = response.choices[0].message.content

            # Extract token usage
            usage = response.usage
            metadata = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
            }

            logger.log_result(
                completion_tokens=metadata["completion_tokens"],
                total_tokens=metadata["total_tokens"],
                finish_reason=metadata["finish_reason"],
            )

        # Log response
        log_llm_response(
            response_text=response_text,
            prompt_tokens=metadata["prompt_tokens"],
            completion_tokens=metadata["completion_tokens"],
            total_tokens=metadata["total_tokens"],
        )

        return response_text, metadata

    def generate_reasoning(
        self,
        query: str,
        context: Dict[str, Any],
        available_tools: list[str],
    ) -> tuple[str, str, str]:
        """
        Generate reasoning for tool selection (ReAct style).

        Args:
            query: User's research query
            context: Current context (history, sources, etc.)
            available_tools: List of available tool names

        Returns:
            Tuple of (thought, action, action_input)

        Raises:
            ValueError: If response cannot be parsed
        """
        # Build reasoning prompt (will be implemented next)
        prompt = self._build_reasoning_prompt(query, context, available_tools)

        # Generate with specific parameters for reasoning
        response_text, metadata = self.generate(
            prompt=prompt,
            temperature=0.7,  # Moderate creativity
            max_tokens=500,   # Short reasoning
        )

        # Parse response
        thought, action, action_input = self._parse_reasoning_response(response_text)

        return thought, action, action_input

    def generate_synthesis(
        self,
        query: str,
        internal_sources: list[str],
        external_sources: list[Dict[str, Any]],
        reasoning_trace: list[Dict[str, Any]],
    ) -> str:
        """
        Generate final research brief synthesizing all sources.

        Args:
            query: User's research query
            internal_sources: Results from internal KB
            external_sources: Results from web search
            reasoning_trace: Agent's reasoning steps

        Returns:
            Markdown-formatted research brief
        """
        # Build synthesis prompt (will be implemented next)
        prompt = self._build_synthesis_prompt(
            query, internal_sources, external_sources, reasoning_trace
        )

        # Generate with specific parameters for synthesis
        response_text, metadata = self.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=2000,  # Longer for detailed answer
        )

        return response_text

    def _build_reasoning_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        available_tools: list[str],
    ) -> str:
        """Build ReAct-style reasoning prompt."""
        # Get what's been done so far
        internal_done = any(
            call.get("tool") == "search_internal"
            for call in context.get("tool_calls", [])
        )
        external_done = any(
            call.get("tool") == "web_search"
            for call in context.get("tool_calls", [])
        )

        # Build context description with actual content previews
        context_desc = []

        # Show KB path and document list if available
        kb_path = context.get("kb_path")
        if kb_path:
            from pathlib import Path
            kb_path_obj = Path(kb_path)
            context_desc.append(f"- Knowledge base available at: {kb_path}")

            # List documents in KB to help LLM understand topic area
            if kb_path_obj.exists():
                doc_files = []
                for ext in ['*.md', '*.txt', '*.pdf']:
                    doc_files.extend(kb_path_obj.rglob(ext))

                if doc_files:
                    # Show first few filenames to indicate topic
                    file_names = [f.name for f in doc_files[:10]]
                    context_desc.append(f"  Documents in KB: {', '.join(file_names)}")
                    if len(doc_files) > 10:
                        context_desc.append(f"  (and {len(doc_files) - 10} more documents)")
                else:
                    context_desc.append(f"  (KB directory is empty or contains no .md/.txt/.pdf files)")

        # Show internal search results with content preview
        if internal_done:
            internal_sources = context.get("internal_context", [])
            num_internal = len(internal_sources)
            if num_internal > 0:
                # Show first result preview so LLM can judge relevance
                first_preview = internal_sources[0][:200] + "..." if internal_sources else ""
                context_desc.append(f"- Internal KB search completed: {num_internal} sources retrieved")
                context_desc.append(f"  Preview of first result: {first_preview}")
            else:
                context_desc.append(f"- Internal KB search completed: No relevant results found")

        # Show web search results with content preview
        if external_done:
            external_sources = context.get("external_context", [])
            num_external = len(external_sources)
            if num_external > 0:
                # Show first few results with title and content preview
                first_result = external_sources[0]
                title = first_result.get('title', 'Untitled')
                content = first_result.get('content', '')[:150]
                context_desc.append(f"- Web search COMPLETED: {num_external} sources retrieved")
                context_desc.append(f"  Sample result: '{title}'")
                context_desc.append(f"  Content preview: {content}...")
            else:
                context_desc.append(f"- Web search completed: No results found")

        context_str = "\n".join(context_desc) if context_desc else "- No searches performed yet"

        prompt = f"""You are a research agent that helps answer questions by using available tools.

**Research Query:** {query}

**Current Context:**
{context_str}

**Available Tools:**
{', '.join(available_tools)}

**Available Actions:**
- search_internal: Search the internal knowledge base (local documents about specific topics)
- web_search: Search the web for current information, people, events, or topics not in KB
- finish: Generate final answer when you have enough information

**Your Task:**
Analyze the query and current context, then decide what to do next. Use this format:

THOUGHT: [Your reasoning about what to do next]
ACTION: [One of: search_internal, web_search, finish]
ACTION_INPUT: [The query to use for the action]

**CRITICAL DECISION RULES (follow in order):**

1. **CHECK IF ALREADY DONE**: Look at "Current Context" above
   - If web_search COMPLETED with results → USE FINISH (don't search again!)
   - If search_internal COMPLETED with results → check if relevant

2. **EVALUATE WHAT YOU HAVE**:
   - Read the content previews shown above
   - If results answer the query → USE FINISH immediately
   - If results are irrelevant (e.g., quantum docs for person query) → try other tool

3. **AVOID WASTED SEARCHES**:
   - NEVER use search_internal OR web_search if that tool already returned results
   - Repeating the same search wastes time and money
   - If you have ANY relevant results, proceed to FINISH

4. **TOOL SELECTION** (only if no searches done yet):
   - Look at "Knowledge base available at:" and "Documents in KB:" listed above
   - Read the document filenames to understand what topics the KB covers
   - Ask yourself: "Does my query match the topics covered in these documents?"
   - Examples:
     * Query "who is John Doe?" + KB contains "quantum_computing.md, classical_computing.md" → NO MATCH → use web_search
     * Query "what is quantum entanglement?" + KB contains "quantum_computing.md" → LIKELY MATCH → use search_internal
     * Query "latest news 2024" + any KB → NO MATCH (needs current info) → use web_search
     * Query "explain neural networks" + KB contains "deep_learning.md, neural_nets.md" → MATCH → use search_internal
   - Use your reasoning: match query topic to document names, don't search KB for clearly unrelated topics

**REMEMBER**: If you see "Web search COMPLETED: X sources" or "Internal KB search completed: X sources"
in Current Context above, you MUST use ACTION: finish (not search again).

Now, what should we do next?"""

        return prompt

    def _parse_reasoning_response(self, response: str) -> tuple[str, str, str]:
        """
        Parse LLM reasoning response into components.

        Expected format:
        THOUGHT: ...
        ACTION: ...
        ACTION_INPUT: ...
        """
        thought = ""
        action = "finish"  # Default
        action_input = ""

        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("THOUGHT:"):
                thought = line.replace("THOUGHT:", "").strip()
            elif line.startswith("ACTION:"):
                action_text = line.replace("ACTION:", "").strip().lower()
                # Normalize action name
                if "internal" in action_text or "search_internal" in action_text:
                    action = "search_internal"
                elif "web" in action_text or "web_search" in action_text:
                    action = "web_search"
                elif "finish" in action_text:
                    action = "finish"
            elif line.startswith("ACTION_INPUT:") or line.startswith("ACTION INPUT:"):
                action_input = line.replace("ACTION_INPUT:", "").replace("ACTION INPUT:", "").strip()

        # Validation
        if not thought:
            thought = "Analyzing the query and deciding next steps."
        if not action_input:
            action_input = "No specific input needed"

        return thought, action, action_input

    def _build_synthesis_prompt(
        self,
        query: str,
        internal_sources: list[str],
        external_sources: list[Dict[str, Any]],
        reasoning_trace: list[Dict[str, Any]],
    ) -> str:
        """Build prompt for synthesizing final answer."""

        # Format internal sources
        internal_str = ""
        if internal_sources:
            internal_str = "**Internal Knowledge Base Sources:**\n\n"
            for i, source in enumerate(internal_sources[:5], 1):  # Top 5
                preview = source[:300] + "..." if len(source) > 300 else source
                internal_str += f"{i}. {preview}\n\n"
        else:
            internal_str = "**Internal Knowledge Base Sources:** None\n\n"

        # Format external sources
        external_str = ""
        if external_sources:
            external_str = "**Web Search Sources:**\n\n"
            for i, source in enumerate(external_sources[:5], 1):  # Top 5
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                content = source.get("content", "")[:300]
                external_str += f"{i}. **{title}**\n   URL: {url}\n   {content}...\n\n"
        else:
            external_str = "**Web Search Sources:** None\n\n"

        prompt = f"""You are a research assistant tasked with creating a comprehensive research brief.

**Research Query:** {query}

{internal_str}

{external_str}

**Your Task:**
Synthesize the information from all sources into a well-structured research brief in Markdown format.

**Required Structure:**

# Research Brief: {query}

## Summary
[2-3 sentences summarizing the key findings]

## Key Findings
[3-5 bullet points with the most important insights from the sources]

## Detailed Analysis
[2-3 paragraphs providing deeper analysis, comparisons, or explanations based on the sources]

## Sources
### Internal Knowledge Base
[List internal sources if used]

### External Web Sources
[List external sources with links if used]

**Guidelines:**
1. Synthesize information from ALL sources, don't just copy
2. Cite sources when making specific claims
3. Be objective and balanced
4. If sources conflict, acknowledge different perspectives
5. Keep language clear and accessible
6. Use markdown formatting for readability

Now, generate the research brief:"""

        return prompt


# Global LLM client instance (singleton pattern)
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

"""
Unified LLM client that supports multiple providers (Anthropic, Azure OpenAI)
"""
import logging
from typing import List, Dict, Optional

from .config import config

logger = logging.getLogger(__name__)


class LLMResponse:
    """Standardized LLM response format"""

    def __init__(self, text: str, model: str, usage: Optional[Dict[str, int]] = None):
        self.text = text
        self.model = model
        self.usage = usage or {}


class LLMClient:
    """Unified LLM client supporting multiple providers (Anthropic Claude, Azure OpenAI)"""

    def __init__(self):
        """Initialize the appropriate LLM client based on config"""
        self.provider = config.LLM_PROVIDER

        if self.provider == "anthropic":
            try:
                from anthropic import Anthropic
            except ImportError as e:
                raise ImportError(
                    "Anthropic package not installed. Install it with: pip install anthropic"
                ) from e

            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self.model = config.CLAUDE_MODEL
            logger.info(f"🤖 Using Anthropic Claude: {self.model}")

        elif self.provider == "azure_openai":
            try:
                from openai import AzureOpenAI
            except ImportError as e:
                raise ImportError(
                    "OpenAI package not installed. Install it with: pip install openai"
                ) from e

            self.client = AzureOpenAI(
                api_key=config.AZURE_OPENAI_API_KEY,
                api_version=config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT
            )
            self.model = config.AZURE_OPENAI_DEPLOYMENT_NAME
            logger.info(f"🤖 Using Azure OpenAI: {self.model}")

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def create_message(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 0.0,
        system: Optional[str] = None
    ) -> LLMResponse:
        """
        Create a message completion using the configured LLM provider

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0 = deterministic)
            system: System prompt (optional)

        Returns:
            LLMResponse with standardized format
        """
        if self.provider == "anthropic":
            return self._anthropic_create(messages, max_tokens, temperature, system)
        elif self.provider == "azure_openai":
            return self._azure_openai_create(messages, max_tokens, temperature, system)

    def _anthropic_create(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        system: Optional[str]
    ) -> LLMResponse:
        """Call Anthropic Claude API"""
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }

            if system:
                kwargs["system"] = system

            logger.debug(f"Calling Anthropic API with model={self.model}")
            response = self.client.messages.create(**kwargs)

            # Extract text from response
            text = response.content[0].text

            # Extract usage info
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

            logger.info(f"Anthropic API call successful. Usage: {usage}")
            return LLMResponse(text=text, model=self.model, usage=usage)

        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    def _azure_openai_create(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        system: Optional[str]
    ) -> LLMResponse:
        """Call Azure OpenAI API"""
        try:
            # Add system message if provided
            api_messages = []
            if system:
                api_messages.append({"role": "system", "content": system})
            api_messages.extend(messages)

            logger.debug(f"Calling Azure OpenAI API with model={self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # Extract text from response
            text = response.choices[0].message.content

            # Extract usage info
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            logger.info(f"Azure OpenAI API call successful. Usage: {usage}")
            return LLMResponse(text=text, model=self.model, usage=usage)

        except Exception as e:
            logger.error(f"Azure OpenAI API call failed: {e}")
            raise

    def get_model_name(self) -> str:
        """Get the current model name"""
        return self.model

    def get_provider(self) -> str:
        """Get the current provider name"""
        return self.provider

"""
Unified LLM client that supports multiple providers (Anthropic, Azure OpenAI)
"""
import json
import logging
import re
from typing import Any, List, Dict, Optional

from core.utils.config import config

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

    # ============= Reasoning Methods for Hypothesis-Driven Investigation =============

    RCA_SYSTEM_PROMPT = """You are an expert RCA (Root Cause Analysis) agent for FourKites shipment tracking.

Your role is to analyze shipment tracking issues and determine root causes. You have deep knowledge of:
- Ocean shipment tracking workflows
- Carrier portal integrations (JustTransform/JT scraping)
- Network relationships between shippers and carriers
- Tracking configuration and subscription management
- Common failure patterns and their root causes

When reasoning:
1. Think step-by-step
2. Consider multiple hypotheses
3. Be specific and actionable
4. Format responses as JSON when asked
5. Update confidence levels based on evidence

Common root causes you should consider:
- network_relationship_missing: Shipper-carrier relationship not set up in the system
- network_relationship_inactive: Relationship exists but is inactive/expired
- jt_scraping_error: JustTransform (RPA) failed to scrape carrier portal correctly
- jt_formatting_error: JT scraped data correctly but formatting/transformation failed
- carrier_portal_down: Carrier's tracking portal is unavailable
- carrier_data_incorrect: Carrier portal shows wrong/stale data
- subscription_inactive: Tracking subscription is not active
- identifier_mismatch: Container/booking number doesn't match carrier records
- system_processing_error: Internal system error in event processing
"""

    def reason(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Use LLM for reasoning and analysis (not just extraction).

        Args:
            prompt: The reasoning prompt
            max_tokens: Maximum tokens in response

        Returns:
            LLM's reasoning response as string
        """
        messages = [{"role": "user", "content": prompt}]

        response = self.create_message(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,  # Low but not zero for reasoning
            system=self.RCA_SYSTEM_PROMPT
        )

        return response.text

    def reason_json(self, prompt: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Use LLM for reasoning and return parsed JSON.

        Args:
            prompt: The reasoning prompt (should ask for JSON output)
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response as dict
        """
        # Add JSON formatting instruction
        json_prompt = f"{prompt}\n\nRespond with valid JSON only. No markdown, no explanation outside JSON."

        text = self.reason(json_prompt, max_tokens)

        # Try to parse JSON
        try:
            # Extract JSON from potential markdown code blocks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if json_match:
                text = json_match.group(1)

            # Try direct parse
            return json.loads(text.strip())

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {text[:500]}...")

            # Try to extract JSON object/array from text
            json_pattern = re.search(r'[\[{][\s\S]*[\]}]', text)
            if json_pattern:
                try:
                    return json.loads(json_pattern.group())
                except json.JSONDecodeError:
                    pass

            # Return empty dict with error
            return {"error": "Failed to parse JSON", "raw_response": text[:500]}

    def extract_identifiers(self, subject: str, description: str) -> Dict[str, Any]:
        """
        Extract shipment identifiers from ticket text.

        Args:
            subject: Ticket subject line
            description: Ticket description

        Returns:
            Dict with extracted identifiers
        """
        prompt = f"""Extract shipment identifiers from this support ticket:

Subject: {subject}

Description: {description}

Look for and extract these identifiers (if present):
- load_id: FourKites load/tracking ID (numeric)
- load_number: Customer's load reference number
- container_number: Ocean container number (e.g., MSCU1234567)
- booking_number: Carrier booking reference
- bill_of_lading: B/L number
- carrier_name: Shipping carrier name
- shipper_name: Shipper/customer company name
- tracking_number: Any tracking reference

Return as JSON with only the identifiers found. Use null for not found.
"""

        return self.reason_json(prompt)

    def synthesize_root_cause(
        self,
        hypotheses: List[Dict[str, Any]],
        all_evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize final root cause from all hypotheses and evidence.

        Args:
            hypotheses: List of hypothesis dicts with status and confidence
            all_evidence: List of evidence dicts from all sub-agents

        Returns:
            Synthesis with root_cause, confidence, actions, uncertainties
        """
        # Format hypotheses for prompt
        hyp_text = "\n".join([
            f"- {h.get('description', 'Unknown')} "
            f"[status={h.get('status', 'unknown')}, confidence={h.get('confidence', 0):.2f}]"
            for h in hypotheses
        ])

        # Format evidence
        evidence_text = "\n".join([
            f"- {e.get('finding', 'Unknown finding')} "
            f"[source={e.get('source', 'unknown')}]"
            for e in all_evidence[:20]  # Limit to first 20
        ])

        prompt = f"""We investigated multiple hypotheses in parallel:

HYPOTHESES TESTED:
{hyp_text}

EVIDENCE COLLECTED:
{evidence_text}

Based on all the evidence, synthesize the final root cause analysis.

Return JSON with:
{{
    "root_cause": "<most likely root cause description>",
    "root_cause_type": "<type: network_relationship_missing|jt_scraping_error|carrier_portal_down|etc>",
    "confidence": <0.0-1.0>,
    "explanation": "<detailed explanation of why this is the root cause>",
    "recommended_actions": ["<action 1>", "<action 2>"],
    "remaining_uncertainties": ["<uncertainty 1>", "<uncertainty 2>"]
}}
"""

        return self.reason_json(prompt, max_tokens=1500)

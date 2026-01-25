"""
Identifier Extraction Agent
Uses LLM to extract tracking IDs, load numbers, containers, and other identifiers from issue text
"""
import json
import logging
from typing import Dict, Any

from app.agents.base import BaseAgent
from app.models import InvestigationState, TransportMode
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class IdentifierAgent(BaseAgent):
    """Extracts identifiers from issue description using LLM"""

    def __init__(self):
        super().__init__("Identifier Agent")
        self.llm_client = LLMClient()

    async def execute(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Extract identifiers from issue text

        Returns:
            State updates with:
            - identifiers: Dict with tracking_id, load_number, container, etc.
            - transport_mode: Detected transport mode
            - issue_category: Issue category
        """
        issue_text = state.get("issue_text", "")
        manual_ids = state.get("manual_identifiers", {})

        if not issue_text and not manual_ids:
            return {
                "identifiers": {},
                "transport_mode": TransportMode.UNKNOWN,
                "issue_category": "unknown",
                "_message": "No issue text or manual identifiers provided"
            }

        # If manual identifiers provided, use them directly
        if manual_ids:
            identifiers = manual_ids
            mode = self._detect_mode(identifiers)
            return {
                "identifiers": identifiers,
                "transport_mode": mode,
                "_message": f"Using manual identifiers: {list(identifiers.keys())}"
            }

        # Use LLM to extract identifiers
        prompt = self._build_extraction_prompt(issue_text)

        try:
            response = self.llm_client.create_message(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.0
            )

            # Parse JSON response from LLMResponse object
            # Strip markdown code blocks if present
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()

            result = json.loads(response_text)

            # Build identifiers dict
            identifiers = {}

            # Tracking IDs (most critical)
            if result.get("tracking_ids"):
                identifiers["tracking_id"] = result["tracking_ids"][0]  # Primary
                if len(result["tracking_ids"]) > 1:
                    identifiers["additional_tracking_ids"] = result["tracking_ids"][1:]

            # Load numbers
            if result.get("load_numbers"):
                identifiers["load_number"] = result["load_numbers"][0]
                if len(result["load_numbers"]) > 1:
                    identifiers["additional_load_numbers"] = result["load_numbers"][1:]

            # Container (Ocean)
            if result.get("container"):
                identifiers["container"] = result["container"]

            # Vessel (Ocean)
            if result.get("vessel"):
                identifiers["vessel"] = result["vessel"]

            # PRO number
            if result.get("pro_numbers"):
                identifiers["pro_number"] = result["pro_numbers"][0]

            # Company names
            if result.get("shipper_name"):
                identifiers["shipper_name"] = result["shipper_name"]

            if result.get("carrier_name"):
                identifiers["carrier_name"] = result["carrier_name"]

            # Dates
            if result.get("dates_mentioned"):
                identifiers["dates_mentioned"] = result["dates_mentioned"]

            # Detect transport mode
            mode = self._detect_mode(identifiers)

            # Issue category
            issue_category = result.get("issue_category", "unknown")

            summary_parts = []
            if identifiers.get("tracking_id"):
                summary_parts.append(f"tracking_id={identifiers['tracking_id']}")
            if identifiers.get("load_number"):
                summary_parts.append(f"load_number={identifiers['load_number']}")
            if identifiers.get("container"):
                summary_parts.append(f"container={identifiers['container']}")

            summary = f"Extracted: {', '.join(summary_parts) if summary_parts else 'no identifiers found'}"

            return {
                "identifiers": identifiers,
                "transport_mode": mode,
                "issue_category": issue_category,
                "_message": summary
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            return {
                "identifiers": {},
                "transport_mode": TransportMode.UNKNOWN,
                "issue_category": "unknown",
                "_message": f"LLM extraction failed: Invalid JSON response"
            }
        except Exception as e:
            logger.error(f"Identifier extraction error: {str(e)}")
            return {
                "identifiers": {},
                "transport_mode": TransportMode.UNKNOWN,
                "issue_category": "unknown",
                "_message": f"Extraction error: {str(e)}"
            }

    def _build_extraction_prompt(self, issue_text: str) -> str:
        """Build LLM prompt for identifier extraction"""
        return f"""You are a logistics data extraction specialist. Extract ALL relevant identifiers from this support issue.

**Issue Description:**
{issue_text[:3000]}

**EXTRACTION RULES:**

1. **tracking_id**: Internal system tracking ID (8-10 digit numbers)
   - Look for: "tracking_id=xxx", "load_id=xxx", "load: xxx", "Load Example: xxx"
   - When in doubt, put it in tracking_id

2. **load_number**: External customer load number (alphanumeric)
   - Only extract if explicitly says: "customer load number", "external load number", "shipper's load number"

3. **container**: Container number (for ocean shipments)
   - Format: Letters followed by numbers (e.g., MSCU1234567)

4. **vessel**: Vessel name or number (for ocean)

5. **pro_number**: PRO/BOL number from carrier

6. **shipper_name**: Customer/shipper company name

7. **carrier_name**: Trucking/carrier company name

8. **dates_mentioned**: ALL dates in the issue
   - Format: [{{"date": "YYYY-MM-DD", "context": "description"}}]

**ISSUE CATEGORIES:**
- load_creation_failure
- load_update_failure
- eta_calculation_issue
- carrier_update_missing
- callback_webhook_failure
- timeout_performance
- configuration_issue
- data_quality_issue
- ocean_tracking_issue
- other

**OUTPUT FORMAT (JSON only, no markdown):**
{{
  "issue_category": "category_name",
  "tracking_ids": [],
  "load_numbers": [],
  "pro_numbers": [],
  "shipper_name": null,
  "carrier_name": null,
  "vessel": null,
  "container": null,
  "dates_mentioned": []
}}

Return ONLY the JSON object, no explanations."""

    def _detect_mode(self, identifiers: Dict[str, Any]) -> TransportMode:
        """Detect transport mode from identifiers"""
        if identifiers.get("container") or identifiers.get("vessel"):
            return TransportMode.OCEAN

        # Could add more heuristics here
        # For now, default to UNKNOWN
        return TransportMode.UNKNOWN

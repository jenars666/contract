import os
import json
import uuid
from typing import List, Dict
from llm.prompts import AUDIT_PROMPT, AUDIT_USER_PROMPT_TEMPLATE
from utils.logger import get_logger

logger = get_logger("analyzer.audit_engine")

def run_semantic_audit(code: str) -> List[Dict]:
    """
    Performs a deep semantic audit using LLM to find logic flaws and advanced exploits.
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    
    if provider == "openrouter":
        return _audit_openrouter(code)
    else:
        return _audit_anthropic(code)

def _audit_openrouter(code: str) -> List[Dict]:
    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package missing; semantic audit unavailable")
        return []

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY missing; semantic audit unavailable")
        return []

    model_name = os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet")
    user_prompt = AUDIT_USER_PROMPT_TEMPLATE.format(code=code)

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": AUDIT_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            response_format={ "type": "json_object" } if "gpt" in model_name.lower() else None
        )

        content = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            import re
            content = re.sub(r"^```[a-zA-Z0-9_\-]*\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
            content = content.strip()
            
        return _parse_audit_json(content)
    except Exception as exc:
        logger.error("OpenRouter semantic audit failed: %s", exc)
        return []

def _audit_anthropic(code: str) -> List[Dict]:
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package missing; semantic audit unavailable")
        return []

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing; semantic audit unavailable")
        return []

    model_name = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    user_prompt = AUDIT_USER_PROMPT_TEMPLATE.format(code=code)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name,
            max_tokens=4096,
            temperature=0.0,
            system=AUDIT_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        
        # Strip markdown fences
        content = content.strip()
        if content.startswith("```"):
            import re
            content = re.sub(r"^```[a-zA-Z0-9_\-]*\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
            content = content.strip()

        return _parse_audit_json(content)
    except Exception as exc:
        logger.error("Anthropic semantic audit failed: %s", exc)
        return []

def _parse_audit_json(content: str) -> List[Dict]:
    try:
        data = json.loads(content)
        vulns = data if isinstance(data, list) else data.get("vulnerabilities", [])
        
        # Normalize and add UUIDs
        final_vulns = []
        for v in vulns:
            final_vulns.append({
                "id": str(uuid.uuid4()),
                "type": v.get("type", "semantic-issue"),
                "title": v.get("title", "Advanced Vulnerability"),
                "severity": v.get("severity", "MEDIUM").upper(),
                "lines": v.get("lines", []),
                "description": v.get("description", "Semantic analysis detected a potential issue."),
                "source": "Semantic Audit"
            })
        return final_vulns
    except json.JSONDecodeError as e:
        logger.error("Failed to parse semantic audit JSON: %s. Content: %s", e, content)
        return []

import os
import re

from llm.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, build_vulnerability_details
from utils.logger import get_logger

logger = get_logger("llm.patch_generator")


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_\-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()
def _clean_vulnerability_comments(code: str) -> str:
    """Removes diagnostic comments like // ❌ or // Vulnerability: ..."""
    lines = code.splitlines()
    cleaned_lines = []
    for line in lines:
        # Check for ❌ or common vulnerability labels used in demos
        if any(marker in line for marker in ["❌", "// Vulnerable", "// External call before", "// Unsafe arithmetic", "// logic bug"]):
            # If it's a comment-only line with a marker, skip it
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            # If it's a code line with a comment at the end, strip the comment
            if "//" in line:
                code_part = line.split("//")[0].rstrip()
                if code_part:
                    cleaned_lines.append(code_part)
                continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _extract_security_fixes(code: str) -> list[str]:
    changes = []
    for line in code.splitlines():
        if "// SECURITY FIX:" in line:
            changes.append(line.split("// SECURITY FIX:", 1)[1].strip())
    return changes


def _build_rule_based_patch(original_code: str, vulnerabilities: list) -> dict:
    import re
    patched = original_code
    changes: list[str] = []

    # 2. Fix reentrancy: move state update BEFORE external call (CEI pattern)
    reentrancy_pattern = re.compile(
        r'([ \t]*)\(bool success,\) = msg\.sender\.call\{value: amount\}\(""\);\s*'
        r'require\(success, "Transfer failed"\);\s*'
        r'balances\[msg\.sender\] -= amount;',
        re.DOTALL,
    )
    reentrancy_match = reentrancy_pattern.search(patched)
    if reentrancy_match:
        indent = reentrancy_match.group(1)
        replacement = (
            indent + 'balances[msg.sender] -= amount;\n'
            + indent + '(bool success,) = msg.sender.call{value: amount}("");\n'
            + indent + 'require(success, "Transfer failed");'
        )
        patched = reentrancy_pattern.sub(replacement, patched)
        changes.append("Reentrancy fixed: state update moved before external call (CEI pattern)")

    # 3. Fix tx.origin: replace with msg.sender
    if "tx.origin" in patched:
        patched = patched.replace(
            'require(tx.origin == owner, "Not owner");',
            'require(msg.sender == owner, "Not owner");',
        )
        changes.append("tx.origin replaced with msg.sender")

    # 4. Fix missing access control on setOwner
    setowner_pattern = re.compile(
        r'(function setOwner\(address newOwner\) public \{\s*)(owner = newOwner;)'
    )
    if setowner_pattern.search(patched):
        patched = setowner_pattern.sub(
            lambda m: m.group(1) + 'require(msg.sender == owner, "Not owner");\n        ' + m.group(2),
            patched,
        )
        changes.append("Missing access control fixed on setOwner")

    # 5. Fix unchecked arithmetic: remove unchecked block
    unchecked_pattern = re.compile(
        r'[ \t]*unchecked \{\s*([^}]+)\}',
        re.DOTALL,
    )
    if unchecked_pattern.search(patched):
        def _unwrap_unchecked(m: re.Match) -> str:
            inner = m.group(1).rstrip()
            lines = inner.splitlines()
            result = []
            for line in lines:
                stripped = line.strip()
                if stripped:
                    result.append("        " + stripped)
            return "\n".join(result)
        patched = unchecked_pattern.sub(_unwrap_unchecked, patched)
        changes.append("Unsafe unchecked arithmetic block removed")

    # 6. Clean up any double blank lines introduced
    patched = re.sub(r"\n{3,}", "\n\n", patched)
    
    # 7. Final wash: Remove ❌ emojis and diagnostic comments
    patched = _clean_vulnerability_comments(patched)

    return {
        "patched_code": patched.strip() + "\n",
        "explanation": "\n".join(f"- {c}" for c in changes) if changes else "No changes applied.",
        "changes_summary": changes,
        "model_used": "rule-based-fallback",
        "tokens_used": 0,
    }


def generate_patch(original_code: str, vulnerabilities: list) -> dict:
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    
    if provider == "openrouter":
        return _generate_patch_openrouter(original_code, vulnerabilities)
    else:
        return _generate_patch_anthropic(original_code, vulnerabilities)


def _generate_patch_openrouter(original_code: str, vulnerabilities: list) -> dict:
    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        logger.warning("openai package missing; using fallback patching")
        return _build_rule_based_patch(original_code, vulnerabilities)

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY missing; using fallback patching")
        return _build_rule_based_patch(original_code, vulnerabilities)

    model_name = os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet")
    vulnerability_details = build_vulnerability_details(vulnerabilities)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        vuln_count=len(vulnerabilities),
        original_code=original_code,
        vulnerability_details=vulnerability_details,
    )

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        patched_code = _strip_markdown_fences(response.choices[0].message.content)
        patched_code = _clean_vulnerability_comments(patched_code)

        if not patched_code.startswith("pragma solidity"):
            raise RuntimeError("LLM returned invalid Solidity response format")

        changes_summary = _extract_security_fixes(patched_code)
        explanation = (
            "\n".join(f"- {change}" for change in changes_summary)
            if changes_summary
            else "Patch generated by OpenRouter LLM without explicit SECURITY FIX comments."
        )

        token_usage = getattr(response.usage, "total_tokens", 0)

        return {
            "patched_code": patched_code,
            "explanation": explanation,
            "changes_summary": changes_summary,
            "model_used": model_name,
            "tokens_used": token_usage,
        }
    except Exception as exc:
        logger.error("OpenRouter patch generation failed: %s", exc)
        return _build_rule_based_patch(original_code, vulnerabilities)


def _generate_patch_anthropic(original_code: str, vulnerabilities: list) -> dict:
    try:
        import anthropic
    except ModuleNotFoundError:
        logger.warning("anthropic package missing; using fallback patching")
        return _build_rule_based_patch(original_code, vulnerabilities)

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing; using fallback patching")
        return _build_rule_based_patch(original_code, vulnerabilities)

    model_name = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    vulnerability_details = build_vulnerability_details(vulnerabilities)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        vuln_count=len(vulnerabilities),
        original_code=original_code,
        vulnerability_details=vulnerability_details,
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name,
            max_tokens=4096,
            temperature=0.1,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text_blocks = []
        for block in response.content:
            if hasattr(block, "text"):
                text_blocks.append(block.text)
        patched_code = _strip_markdown_fences("\n".join(text_blocks))
        patched_code = _clean_vulnerability_comments(patched_code)

        if not (patched_code.startswith("pragma solidity") or patched_code.startswith("//")):
            raise anthropic.APIError(message="LLM returned invalid Solidity response format", request=None, body=None)

        changes_summary = _extract_security_fixes(patched_code)
        explanation = (
            "\n".join(f"- {change}" for change in changes_summary)
            if changes_summary
            else "Patch generated by Anthropic LLM without explicit SECURITY FIX comments."
        )

        token_usage = 0
        if getattr(response, "usage", None):
            input_tokens = getattr(response.usage, "input_tokens", 0) or 0
            output_tokens = getattr(response.usage, "output_tokens", 0) or 0
            token_usage = input_tokens + output_tokens

        return {
            "patched_code": patched_code,
            "explanation": explanation,
            "changes_summary": changes_summary,
            "model_used": model_name,
            "tokens_used": token_usage,
        }

    except anthropic.AuthenticationError as exc:
        raise RuntimeError("Invalid API key") from exc
    except anthropic.RateLimitError as exc:
        raise RuntimeError("Rate limit — wait 30 seconds") from exc
    except anthropic.APIError as exc:
        raise RuntimeError(f"Anthropic API error: {exc}") from exc
    except Exception as exc:
        logger.error("LLM patch generation failed: %s", exc)
        return _build_rule_based_patch(original_code, vulnerabilities)

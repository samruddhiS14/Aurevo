"""Context-sensitive, deterministic off-platform intent rules."""
import re

OFF_PLATFORM_PATTERNS = [
    ("direct_payment_intent", re.compile(
        r"\bpay\s+directly\b|"
        r"\b(?:pay|send|transfer)\s+(?:me|you|us|the\s+freelancer)\s+(?:directly|via|through|using)\b|"
        r"\b(?:send|transfer)\s+(?:a\s+)?payment\s+(?:via|through|using)\s+(?:wise|venmo|cash\s?app|bank\s+transfer)\b|"
        r"\b(?:send|transfer)\s+(?:the\s+)?money\s+(?:to\s+me|to\s+us)\s+(?:via|through|using)\b|"
        r"\b(?:bank\s+transfer|cashapp|cash\s+app|venmo|wise)\s+(?:me|us|instead)\b|"
        r"\b(?:outside|off)\s+(?:of\s+)?(?:aurevo|the\s+platform)\b|"
        r"\bavoid\s+(?:the\s+)?(?:platform|platform\s+fee|fees)\b", re.I)),
    ("external_channel_intent", re.compile(
        r"\b(?:message|contact|call|text|chat|continue|move|switch)\s+(?:me|us|this|our\s+conversation)?\s*"
        r"(?:on|via|through|over|at)\s+(?:whats\s?app|telegram|signal|discord|skype)\b|"
        r"\b(?:let'?s|we\s+can|can\s+we|could\s+we)\s+(?:move|switch)\s+to\s+(?:whats\s?app|telegram|signal|discord|skype)\b|"
        r"\b(?:whats\s?app|telegram|signal|discord|skype)\s+me\b|"
        r"\b(?:let'?s|we\s+can)\s+(?:continue|talk|chat|communicate)\s+(?:on|via|over)\s+"
        r"(?:whats\s?app|telegram|signal|discord|skype)\b", re.I)),
    ("contact_bypass_intent", re.compile(
        r"\b(?:email|mail|call|text)\s+me\s+(?:at|on)\s+"
        r"(?:[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\+?\d[\d\s().-]{7,}\d)\b", re.I)),
]


def off_platform_reasons(content: str) -> list[str]:
    """Return reasons only when a message explicitly indicates bypass intent."""
    message = (content or "").strip()
    return [name for name, pattern in OFF_PLATFORM_PATTERNS if pattern.search(message)]

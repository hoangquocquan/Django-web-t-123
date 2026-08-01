"""Policy AI có cấu trúc, rule ID và version thay cho regex rời rạc."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AIPolicyContext:
    user_email: str = ""
    role: str = ""
    organization_id: str = ""
    module: str = ""
    endpoint: str = ""
    action: str = ""
    tool: str = ""
    request_source: str = "api"
    policy_version: str = "ai-policy-v2.0"


@dataclass(frozen=True)
class AIPolicyRule:
    rule_id: str
    category: str
    patterns: tuple[str, ...]
    message: str = "Prompt blocked by AI safety policy."

    def matches(self, text):
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in self.patterns)


DEFAULT_POLICY_RULES = (
    AIPolicyRule(
        "INJECTION-001",
        "instruction_override",
        (
            r"\bignore\s+(all\s+)?previous\s+instructions\b",
            r"\b(bỏ|bo)\s+qua\s+(mọi|moi|toàn bộ|toan bo)?\s*(chỉ dẫn|chi dan|hướng dẫn|huong dan)\s+(trước|truoc)\b",
        ),
    ),
    AIPolicyRule(
        "PROMPT-EXFIL-001",
        "prompt_exfiltration",
        (
            r"\breveal\s+(the\s+)?(system|developer)\s+prompt\b",
            r"\b(tiết lộ|tiet lo|hiển thị|hien thi)\s+.*(prompt|chỉ dẫn|chi dan)\s+(hệ thống|he thong)\b",
        ),
    ),
    AIPolicyRule(
        "SECRET-EXFIL-001",
        "secret_extraction",
        (
            r"\b(show|reveal|extract|list)\s+.*(api[_ -]?key|secret|password|token|authorization)\b",
            r"\b(hiển thị|hien thi|tiết lộ|tiet lo|trích xuất|trich xuat)\s+.*(khóa api|khoa api|mật khẩu|mat khau|token|bí mật|bi mat)\b",
        ),
    ),
    AIPolicyRule(
        "DANGEROUS-WRITE-001",
        "dangerous_business_action",
        (
            r"\b(delete|drop|erase)\s+.*(database|customer|quotation|order)\b",
            r"\b(xóa|xoa)\s+.*(cơ sở dữ liệu|co so du lieu|khách hàng|khach hang|báo giá|bao gia|đơn hàng|don hang)\b",
        ),
    ),
    AIPolicyRule(
        "AUTONOMY-001",
        "autonomous_action",
        (
            r"\bauto(?:matically)?\s+(send|approve|merge|deploy|update)\b",
            r"\b(tự động|tu dong)\s+(gửi|gui|duyệt|duyet|triển khai|trien khai|cập nhật|cap nhat)\b",
        ),
    ),
    AIPolicyRule(
        "SHUTDOWN-001",
        "shutdown",
        (
            r"\bshutdown\s+(legacy|production|server)\b",
            r"\b(tắt|tat|dừng|dung)\s+.*(production|máy chủ|may chu|legacy)\b",
        ),
    ),
)


class AIPolicyEngine:
    """Đánh giá normalized input và trả danh sách rule ID đã khớp."""

    def __init__(self, rules=None, version="ai-policy-v2.0"):
        self.rules = tuple(rules or DEFAULT_POLICY_RULES)
        self.version = version

    def evaluate(self, text, context):
        matched = [rule for rule in self.rules if rule.matches(text)]
        return {
            "allowed": not matched,
            "matched_rule_ids": [rule.rule_id for rule in matched],
            "message": matched[0].message if matched else "Policy checks passed.",
            "policy_version": context.policy_version or self.version,
        }

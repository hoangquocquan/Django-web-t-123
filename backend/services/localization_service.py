import hashlib
import html
import logging
import urllib.error
from html.parser import HTMLParser

from config.settings import OLLAMA_MODEL
from repositories import translation_repository
from services.ai_service import AI_PROVIDER, call_ollama


LOGGER = logging.getLogger("mecprecision.localization")

# Ngôn ngữ public site hỗ trợ trong demo này.
# vi không cần dịch vì nội dung gốc của website đang là tiếng Việt.
SUPPORTED_LANGUAGES = {
    "vi": {"label": "Tiếng Việt", "ollama_name": "Vietnamese", "html_lang": "vi"},
    "en": {"label": "English", "ollama_name": "English", "html_lang": "en"},
    "ja": {"label": "日本語", "ollama_name": "Japanese", "html_lang": "ja"},
}

# Các thẻ này chứa code/script/style, nếu dịch sẽ dễ làm hỏng website.
SKIP_TRANSLATION_TAGS = {"script", "style", "code", "pre", "textarea"}

# Nếu Ollama lỗi trong một lần render, ta tạm tắt auto-translate để trang không bị chậm vì nhiều timeout.
AUTO_TRANSLATION_AVAILABLE = True

# Một số nhãn menu quan trọng nên có bản dịch cố định.
# Lý do: menu là phần khách nhìn thấy đầu tiên, không nên phụ thuộc hoàn toàn vào câu trả lời ngẫu nhiên của AI.
MANUAL_TRANSLATIONS = {
    "en": {
        "Trang chủ": "Home",
        "Sản phẩm": "Products",
        "Công nghệ": "Technology",
        "Tin tức": "News",
        "Giới thiệu": "About",
        "Năng lực sản xuất": "Capabilities",
        "Tuyển dụng": "Careers",
        "Liên hệ": "Contact",
        "Đăng nhập": "Login",
    },
    "ja": {
        "Trang chủ": "ホーム",
        "Sản phẩm": "製品",
        "Công nghệ": "技術",
        "Tin tức": "ニュース",
        "Giới thiệu": "会社概要",
        "Năng lực sản xuất": "生産能力",
        "Tuyển dụng": "採用情報",
        "Liên hệ": "お問い合わせ",
        "Đăng nhập": "ログイン",
    },
}


def normalize_language(language):
    """Chuẩn hóa mã ngôn ngữ từ URL, ví dụ ?lang=en hoặc ?lang=ja."""
    language = str(language or "vi").lower().strip()
    return language if language in SUPPORTED_LANGUAGES else "vi"


def build_language_url(path, language):
    """Tạo URL đổi ngôn ngữ cho menu header."""
    language = normalize_language(language)
    if language == "vi":
        return path
    return f"{path}?lang={language}"


def keep_language_in_href(href, language):
    """Giữ lang=en/lang=ja khi người dùng bấm link nội bộ trong trang public."""
    language = normalize_language(language)
    href = str(href or "")
    if language == "vi":
        return href
    if not href.startswith("/") or href.startswith("/admin") or href.startswith("/api") or "." in href.split("/")[-1] and not href.endswith(".html"):
        return href
    if "lang=" in href:
        return href
    separator = "&" if "?" in href else "?"
    return f"{href}{separator}lang={language}"


def get_language_meta(language):
    """Lấy thông tin hiển thị của một ngôn ngữ."""
    return SUPPORTED_LANGUAGES[normalize_language(language)]


def source_hash(text):
    """Tạo mã hash ngắn để cache bản dịch theo nội dung gốc."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_manual_translation(text, target_language):
    """Ưu tiên bản dịch cố định cho menu/nút quan trọng trước khi gọi Ollama."""
    target_language = normalize_language(target_language)
    stripped = str(text or "").strip()
    translated = MANUAL_TRANSLATIONS.get(target_language, {}).get(stripped)
    if not translated:
        return ""
    return text.replace(stripped, translated, 1)


def clean_translated_text(translated):
    """Làm sạch bản dịch để AI không chèn HTML tag vào giữa text node."""
    cleaned = str(translated or "").strip()
    cleaned = cleaned.replace("<p>", "").replace("</p>", "")
    cleaned = cleaned.replace("<span>", "").replace("</span>", "")
    cleaned = cleaned.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    return cleaned


def should_translate_text(text):
    """Kiểm tra một đoạn text trong HTML có nên dịch hay không."""
    stripped = str(text or "").strip()
    if len(stripped) <= 1:
        return False
    if stripped.startswith("{") or stripped.startswith("["):
        return False
    if stripped in {"VI", "EN", "JA", "|"}:
        return False
    return any(character.isalpha() for character in stripped)


def translate_visible_text(text, target_language, model=None):
    """Dịch một đoạn chữ hiển thị và lưu cache SQLite."""
    global AUTO_TRANSLATION_AVAILABLE
    target_language = normalize_language(target_language)
    if target_language == "vi" or not should_translate_text(text):
        return text

    model = model or OLLAMA_MODEL
    stripped = text.strip()
    manual_translation = get_manual_translation(text, target_language)
    if manual_translation:
        return manual_translation

    cached = translation_repository.get_cached_translation(source_hash(stripped), target_language, model)
    if cached:
        return text.replace(stripped, cached["translated_text"], 1)

    if not AUTO_TRANSLATION_AVAILABLE:
        return text

    target_name = SUPPORTED_LANGUAGES[target_language]["ollama_name"]
    prompt = f"""
You are translating visible website text for MecPrecision VIETNAM.
Translate from Vietnamese to {target_name}.
Keep company names, product codes, URLs, numbers, measurement units, HTML entities, CNC terms, and brand names unchanged when appropriate.
Return only the translated text, no explanation.

Text:
{stripped}
"""
    status = "ok"
    error = ""
    try:
        translated = call_ollama(prompt, model).strip()
        translated = clean_translated_text(translated)
        if not translated:
            raise ValueError("Ollama returned empty translation.")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        # Nếu AI lỗi, giữ nguyên tiếng Việt để trang không bị hỏng.
        translated = stripped
        AUTO_TRANSLATION_AVAILABLE = False
        status = "fallback"
        error = str(exc)
        LOGGER.warning(
            "AI_TRANSLATION_FALLBACK target=%s model=%s source=%r error=%s",
            target_language,
            model,
            stripped[:120],
            error,
        )

    if status == "ok":
        translation_repository.save_cached_translation(
            {
                "source_hash": source_hash(stripped),
                "source_text": stripped,
                "target_language": target_language,
                "translated_text": translated,
                "provider": AI_PROVIDER,
                "model": model,
                "status": status,
                "error": error,
            }
        )
    return text.replace(stripped, translated, 1)


class PublicHtmlTranslator(HTMLParser):
    """HTMLParser nhỏ để dịch text node nhưng giữ nguyên cấu trúc HTML."""

    def __init__(self, target_language):
        super().__init__(convert_charrefs=False)
        self.target_language = normalize_language(target_language)
        self.output = []
        self.skip_stack = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TRANSLATION_TAGS:
            self.skip_stack.append(tag)
        self.output.append(self.format_start_tag(tag, attrs, closed=False))

    def handle_startendtag(self, tag, attrs):
        self.output.append(self.format_start_tag(tag, attrs, closed=True))

    def handle_endtag(self, tag):
        if self.skip_stack and self.skip_stack[-1] == tag:
            self.skip_stack.pop()
        self.output.append(f"</{tag}>")

    def handle_data(self, data):
        if self.skip_stack:
            self.output.append(data)
            return
        self.output.append(translate_visible_text(data, self.target_language))

    def handle_entityref(self, name):
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        self.output.append(f"&#{name};")

    def handle_comment(self, data):
        self.output.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.output.append(f"<!{decl}>")

    def format_start_tag(self, tag, attrs, closed=False):
        normalized_attrs = []
        is_language_switch = any(name == "data-language-switch" for name, value in attrs)
        for name, value in attrs:
            if tag == "a" and name == "href" and value is not None and not is_language_switch:
                value = keep_language_in_href(value, self.target_language)
            normalized_attrs.append((name, value))
        attr_html = "".join(
            f' {name}="{html.escape(value, quote=True)}"' if value is not None else f" {name}"
            for name, value in normalized_attrs
        )
        suffix = " />" if closed else ">"
        return f"<{tag}{attr_html}{suffix}"

    def get_html(self):
        return "".join(self.output)


def translate_public_html(html_text, target_language):
    """Dịch toàn bộ HTML public sang ngôn ngữ được chọn."""
    global AUTO_TRANSLATION_AVAILABLE
    AUTO_TRANSLATION_AVAILABLE = True
    target_language = normalize_language(target_language)
    if target_language == "vi":
        return html_text

    parser = PublicHtmlTranslator(target_language)
    parser.feed(html_text)
    parser.close()
    return parser.get_html().replace('<html lang="vi"', f'<html lang="{SUPPORTED_LANGUAGES[target_language]["html_lang"]}"', 1)

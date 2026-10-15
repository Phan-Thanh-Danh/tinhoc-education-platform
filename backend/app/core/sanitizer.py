# filepath: backend/app/core/sanitizer.py
from __future__ import annotations

import re
import bleach

# Danh sách các thẻ HTML an toàn cho phép hiển thị nội dung bài học, code và công thức toán học
ALLOWED_TAGS = [
    "a",
    "b",
    "blockquote",
    "br",
    "code",
    "dd",
    "div",
    "dl",
    "dt",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "img",
    "kbd",
    "li",
    "ol",
    "p",
    "pre",
    "s",
    "samp",
    "small",
    "span",
    "strike",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
    "var",
]

# Các thuộc tính HTML được phép cho từng thẻ (chặn inline style trần để chống CSS injection)
ALLOWED_ATTRIBUTES = {
    "*": ["class", "id", "title"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "code": ["class"],
    "span": ["class", "aria-hidden"],
    "td": ["colspan", "rowspan", "align"],
    "th": ["colspan", "rowspan", "align", "scope"],
}

# Các giao thức an toàn trong URL
ALLOWED_PROTOCOLS = ["http", "https", "mailto", "data"]


def clean_html_content(raw_html: str | None) -> str:
    """
    Làm sạch nội dung HTML / Markdown đã biên dịch để chống mã độc XSS.
    Giữ lại các thẻ hợp lệ phục vụ hiển thị cú pháp code (PrismJS) và toán học (KaTeX).
    """
    if not raw_html:
        return ""

    # Dùng bleach để lọc các thẻ và thuộc tính nguy hiểm (script, onerror, onload, iframe...)
    cleaned = bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )

    # Đảm bảo các liên kết ngoài đều có rel="noopener noreferrer" để chống Tabnabbing
    cleaned = bleach.linkify(
        cleaned,
        callbacks=[
            lambda attrs, new: {
                **attrs,
                (None, "rel"): "noopener noreferrer",
                (None, "target"): "_blank",
            }
        ],
    )

    return cleaned


def clean_plain_text(raw_text: str | None) -> str:
    """
    Khử bỏ hoàn toàn mọi mã HTML đối với các trường văn bản thuần túy
    (Tiêu đề, Tên người dùng, Tên chủ đề, Tag...).
    """
    if not raw_text:
        return ""
    # Tước bỏ toàn bộ thẻ HTML
    cleaned = bleach.clean(raw_text, tags=[], strip=True)
    # Thu gọn khoảng trắng thừa
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

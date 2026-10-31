def strip_html_tags(html: str) -> str:
    import re
    return re.sub(r'<[^>]*>', '', html)

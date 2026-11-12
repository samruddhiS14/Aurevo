from pathlib import Path

_SIGNATURES = {
    ".pdf": (b"%PDF-",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".zip": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
    ".docx": (b"PK\x03\x04",),
    ".xlsx": (b"PK\x03\x04",),
}


def validate_file_content(filename: str, content: bytes) -> bool:
    extension = Path(filename or "").suffix.lower()
    signatures = _SIGNATURES.get(extension)
    if signatures:
        return any(content.startswith(signature) for signature in signatures)
    if extension in (".txt", ".csv"):
        if b"\x00" in content:
            return False
        try:
            content.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False
    return False

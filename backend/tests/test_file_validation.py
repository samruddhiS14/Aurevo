from app.services.file_validation import validate_file_content


def test_pdf_signature_is_required():
    assert validate_file_content("brief.pdf", b"%PDF-1.7 sample")
    assert not validate_file_content("brief.pdf", b"not really a pdf")


def test_image_signatures_are_checked():
    assert validate_file_content("image.png", b"\x89PNG\r\n\x1a\nrest")
    assert validate_file_content("photo.jpg", b"\xff\xd8\xffrest")
    assert not validate_file_content("photo.jpg", b"plain text")


def test_office_documents_and_archives_require_zip_signature():
    assert validate_file_content("document.docx", b"PK\x03\x04rest")
    assert validate_file_content("sheet.xlsx", b"PK\x03\x04rest")
    assert validate_file_content("archive.zip", b"PK\x03\x04rest")
    assert not validate_file_content("document.docx", b"plain text")


def test_text_and_csv_must_be_utf8_without_nul_bytes():
    assert validate_file_content("notes.txt", "Hello, world".encode())
    assert validate_file_content("data.csv", "name,value\nA,1".encode())
    assert not validate_file_content("notes.txt", b"\xff\x00")

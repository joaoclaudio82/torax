import io
import zipfile

from scripts.download_nih_demo import _member_name


def test_member_name_resolves_common_layouts():
    names = ["images/00000001_000.png", "__MACOSX/images/._00000001_000.png"]
    assert _member_name("00000001_000.png", names) == "images/00000001_000.png"


def test_local_zip_roundtrip_extracts_png_bytes():
    buffer = io.BytesIO()
    png = b"\x89PNG\r\n\x1a\n" + b"fake-payload"
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("images/00000002_000.png", png)
    buffer.seek(0)
    with zipfile.ZipFile(buffer) as archive:
        member = _member_name("00000002_000.png", archive.namelist())
        data = archive.read(member)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")

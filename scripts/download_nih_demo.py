"""
Baixa um mini-acervo educacional do NIH ChestX-ray14.

Extrai apenas imagens curadas do arquivo images_001.zip (Hugging Face mirror)
via HTTP Range, sem baixar o ZIP completo (~2 GB).

Fonte oficial: https://nihcc.app.box.com/v/ChestXray-NIHCC
Provedor: NIH Clinical Center.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "nih-demo"
ZIP_URL = (
    "https://huggingface.co/datasets/alkzar90/NIH-Chest-X-ray-dataset/"
    "resolve/main/data/images/images_001.zip"
)
NIH_HOME = "https://nihcc.app.box.com/v/ChestXray-NIHCC"
USER_AGENT = "torax-nih-demo/1.0"

# Casos curados presentes em images_001.zip (rótulos NLP do NIH).
MANIFEST = [
    {
        "id": "nih-no-finding-01",
        "image_index": "00000002_000.png",
        "labels": ["No Finding"],
        "view": "PA",
        "title": "NIH — Sem achado",
        "subtitle": "No Finding · PA",
    },
    {
        "id": "nih-no-finding-02",
        "image_index": "00000005_000.png",
        "labels": ["No Finding"],
        "view": "PA",
        "title": "NIH — Sem achado (2)",
        "subtitle": "No Finding · PA",
    },
    {
        "id": "nih-cardiomegaly",
        "image_index": "00000001_000.png",
        "labels": ["Cardiomegaly"],
        "view": "PA",
        "title": "NIH — Cardiomegalia",
        "subtitle": "Cardiomegaly · PA",
    },
    {
        "id": "nih-atelectasis",
        "image_index": "00000011_006.png",
        "labels": ["Atelectasis"],
        "view": "PA",
        "title": "NIH — Atelectasia",
        "subtitle": "Atelectasis · PA",
    },
    {
        "id": "nih-effusion",
        "image_index": "00000011_000.png",
        "labels": ["Effusion"],
        "view": "PA",
        "title": "NIH — Derrame pleural",
        "subtitle": "Effusion · PA",
    },
    {
        "id": "nih-infiltration",
        "image_index": "00000005_006.png",
        "labels": ["Infiltration"],
        "view": "PA",
        "title": "NIH — Infiltrado",
        "subtitle": "Infiltration · PA",
    },
    {
        "id": "nih-consolidation",
        "image_index": "00000032_016.png",
        "labels": ["Consolidation"],
        "view": "AP",
        "title": "NIH — Consolidação",
        "subtitle": "Consolidation · AP",
    },
    {
        "id": "nih-emphysema",
        "image_index": "00000009_000.png",
        "labels": ["Emphysema"],
        "view": "PA",
        "title": "NIH — Enfisema",
        "subtitle": "Emphysema · PA",
    },
    {
        "id": "nih-nodule",
        "image_index": "00000008_002.png",
        "labels": ["Nodule"],
        "view": "PA",
        "title": "NIH — Nódulo",
        "subtitle": "Nodule · PA",
    },
    {
        "id": "nih-mass",
        "image_index": "00000004_000.png",
        "labels": ["Mass", "Nodule"],
        "view": "AP",
        "title": "NIH — Massa / nódulo",
        "subtitle": "Mass|Nodule · AP",
    },
    {
        "id": "nih-fibrosis",
        "image_index": "00000022_001.png",
        "labels": ["Fibrosis"],
        "view": "PA",
        "title": "NIH — Fibrose",
        "subtitle": "Fibrosis · PA",
    },
    {
        "id": "nih-pleural-thickening",
        "image_index": "00000013_003.png",
        "labels": ["Pleural_Thickening"],
        "view": "AP",
        "title": "NIH — Espessamento pleural",
        "subtitle": "Pleural_Thickening · AP",
    },
    {
        "id": "nih-pneumothorax",
        "image_index": "00000013_023.png",
        "labels": ["Infiltration", "Mass", "Pneumothorax"],
        "view": "AP",
        "title": "NIH — Pneumotórax",
        "subtitle": "Pneumothorax (+ outros) · AP",
    },
    {
        "id": "nih-pneumonia",
        "image_index": "00000056_000.png",
        "labels": ["Nodule", "Pneumonia"],
        "view": "PA",
        "title": "NIH — Pneumonia",
        "subtitle": "Pneumonia|Nodule · PA",
    },
    {
        "id": "nih-edema",
        "image_index": "00000032_001.png",
        "labels": ["Cardiomegaly", "Edema", "Effusion"],
        "view": "AP",
        "title": "NIH — Edema",
        "subtitle": "Edema (+ outros) · AP",
    },
]


class HttpRangeFile:
    """Arquivo remoto com suporte a seek via HTTP Range."""

    def __init__(self, url: str):
        self.url = url
        request = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": USER_AGENT},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            length = response.headers.get("Content-Length")
            if not length:
                raise RuntimeError("Servidor não informou Content-Length.")
            self.size = int(length)
        self.pos = 0

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            self.pos = offset
        elif whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = self.size + offset
        else:
            raise ValueError(f"whence inválido: {whence}")
        return self.pos

    def read(self, n: int = -1) -> bytes:
        if self.pos >= self.size:
            return b""
        if n is None or n < 0:
            end = self.size - 1
        else:
            end = min(self.size - 1, self.pos + n - 1)
        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Range": f"bytes={self.pos}-{end}",
            },
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        self.pos += len(data)
        return data


def _member_name(image_index: str, namelist: list[str]) -> str:
    candidates = [
        f"images/{image_index}",
        image_index,
        f"images_001/{image_index}",
    ]
    for candidate in candidates:
        if candidate in namelist:
            return candidate
    matches = [name for name in namelist if name.endswith(f"/{image_index}")]
    if matches:
        return matches[0]
    raise FileNotFoundError(f"{image_index} não encontrado no ZIP.")


def download_pack() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Abrindo índice remoto: {ZIP_URL}")
    remote = HttpRangeFile(ZIP_URL)
    print(f"Tamanho do ZIP: {remote.size / 1e6:.1f} MB (somente faixas serão baixadas)")

    with zipfile.ZipFile(remote) as archive:
        namelist = archive.namelist()
        saved = []
        for entry in MANIFEST:
            image_index = entry["image_index"]
            destination = OUT_DIR / image_index
            if destination.exists() and destination.stat().st_size > 0:
                print(f"já existe: {image_index}")
            else:
                member = _member_name(image_index, namelist)
                print(f"baixando: {image_index}")
                data = archive.read(member)
                if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError(f"Arquivo inválido: {image_index}")
                destination.write_bytes(data)
            record = {
                **entry,
                "path": f"assets/nih-demo/{image_index}",
                "source": NIH_HOME,
                "provider": "NIH Clinical Center",
                "license_note": (
                    "Uso permitido com atribuição ao NIH Clinical Center. "
                    "Rótulos são minerados por NLP e não constituem laudo."
                ),
                "citation": (
                    "Wang et al., ChestX-ray8, CVPR 2017. "
                    "https://arxiv.org/abs/1705.02315"
                ),
            }
            saved.append(record)

    payload = {
        "dataset": "NIH ChestX-ray14",
        "provider": "NIH Clinical Center",
        "source": NIH_HOME,
        "mirror": ZIP_URL,
        "count": len(saved),
        "images": saved,
        "disclaimer": (
            "Pacote educacional para testes do protótipo. "
            "Não usar para decisão clínica."
        ),
    }
    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Manifesto: {manifest_path}")
    print(f"Concluído: {len(saved)} imagens em {OUT_DIR}")
    return payload


def main() -> int:
    try:
        download_pack()
    except urllib.error.HTTPError as exc:
        print(
            f"Falha HTTP ao acessar o mirror NIH ({exc.code}). "
            f"Verifique a conexão e o espelho Hugging Face / NIH Box.\n"
            f"Detalhe: {exc}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as exc:
        print(
            "Falha de rede ao baixar o mini-banco NIH. "
            "Confira DNS/proxy e tente novamente.\n"
            f"Detalhe: {exc}",
            file=sys.stderr,
        )
        return 1
    except (OSError, RuntimeError, ValueError, FileNotFoundError) as exc:
        print(f"Falha ao baixar o mini-banco NIH: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

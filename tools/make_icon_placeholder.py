"""Gera um ícone placeholder para o Anthocianinas Estabilidade Lab.

Produz ``assets/Antocianinas_Estabilidade_Lab.ico`` a partir de um fundo com
gradiente roxo (pigmento antocianina) e círculos semitransparentes que
representam a dispersão de pigmentos em solução.

Use para substituir o placeholder original, mantendo o mesmo caminho e nome de
arquivo que ``tools/build_windows.ps1`` consome.

    python tools\make_icon_placeholder.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICON_PATH = ASSETS / "Antocianinas_Estabilidade_Lab.ico"
PNG_PATH = ASSETS / "Antocianinas_Estabilidade_Lab.png"


def _gradient_background(size: int) -> Image.Image:
    """Cria um fundo de gradiente roxo-índigo vertical (pigmento)."""
    img = Image.new("RGB", (size, size), (30, 20, 60))
    draw = ImageDraw.Draw(img)
    top = (110, 45, 150)    # roxo claro (antocianina ácida)
    mid = (75, 30, 120)     # roxo médio
    bot = (25, 15, 50)      # índigo escuro
    for y in range(size):
        t = y / (size - 1)
        if t < 0.5:
            u = t / 0.5
            r = int(top[0] + (mid[0] - top[0]) * u)
            g = int(top[1] + (mid[1] - top[1]) * u)
            b = int(top[2] + (mid[2] - top[2]) * u)
        else:
            u = (t - 0.5) / 0.5
            r = int(mid[0] + (bot[0] - mid[0]) * u)
            g = int(mid[1] + (bot[1] - mid[1]) * u)
            b = int(mid[2] + (bot[2] - mid[2]) * u)
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    return img


def _add_pigment_blobs(size: int, img: Image.Image) -> Image.Image:
    """Adiciona círculos semitransparentes representando dispersão de pigmento."""
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    s = size
    blobs = [
        (int(0.30 * s), int(0.32 * s), int(0.16 * s), (220, 90, 200, 140)),
        (int(0.62 * s), int(0.40 * s), int(0.22 * s), (160, 70, 220, 130)),
        (int(0.45 * s), int(0.66 * s), int(0.18 * s), (200, 80, 170, 150)),
        (int(0.70 * s), int(0.72 * s), int(0.12 * s), (120, 60, 180, 120)),
    ]
    for cx, cy, r, color in blobs:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(2, size // 40)))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    size = 256
    base = _gradient_background(size)
    icon_img = _add_pigment_blobs(size, base)

    # Salva PNG de referência.
    icon_img.save(PNG_PATH, format="PNG")

    # Salva ICO com vários tamanhos suportados pelo Windows.
    icon_img.save(
        ICON_PATH,
        format="ICO",
        sizes=[(256, 256), (48, 48), (32, 32), (16, 16)],
    )
    print(f"[OK] Ícone gerado: {ICON_PATH}")
    print(f"[OK] PNG  gerado: {PNG_PATH}")


if __name__ == "__main__":
    main()

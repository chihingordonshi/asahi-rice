#!/usr/bin/env python3
"""Render the looping Linux desktop word carousel for the M1 Touch Bar."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT, FPS = 2008, 60, 30
WORDS = (
    "Linux", "KDE", "Void", "Arch", "Fedora", "NixOS", "GNOME",
    "Hyprland", "Debian", "Ubuntu", "Gentoo", "openSUSE", "Mint",
    "Alpine", "Pop!_OS", "Sway", "i3", "Xfce", "Cinnamon", "Asahi",
    "EndeavourOS", "elementary", "Zorin", "Tails", "LXQt", "Solus",
    "Qubes", "COSMIC",
)
FRAMES_PER_WORD = 36  # 1.2 seconds
SLIDE_FRAMES = 8      # 0.267 seconds; the rest of the interval is still
FRAMES = len(WORDS) * FRAMES_PER_WORD
SPACING = 658
CENTER = WIDTH // 2
SIDE_COLOR = (135, 155, 169)
CENTER_COLOR = (239, 246, 250)


def text_masks(font_path: Path) -> list[Image.Image]:
    if not font_path.is_file():
        raise SystemExit(f"JetBrainsMono Nerd Font Bold was not found: {font_path}")
    scale = 3
    font = ImageFont.truetype(str(font_path), 34 * scale)
    masks = []
    for word in WORDS:
        box = font.getbbox(word)
        mask = Image.new("L", (box[2] - box[0] + 4 * scale, box[3] - box[1] + 4 * scale))
        ImageDraw.Draw(mask).text((2 * scale - box[0], 2 * scale - box[1]), word, font=font, fill=255)
        masks.append(mask.resize((mask.width // scale, mask.height // scale), Image.Resampling.LANCZOS))
    return masks


def make_background() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        draw.line((0, y, WIDTH, y), fill=(round(7 + 7 * t), round(12 + 8 * t), round(20 + 10 * t)))
    draw.line((0, 0, WIDTH, 0), fill=(31, 49, 57))
    draw.line((0, HEIGHT - 1, WIDTH, HEIGHT - 1), fill=(28, 45, 53))
    return image


def slide_progress(frame: int) -> float:
    phase = frame % FRAMES_PER_WORD
    start = FRAMES_PER_WORD - SLIDE_FRAMES
    if phase < start:
        return 0.0
    t = (phase - start + 1) / SLIDE_FRAMES
    return t * t * (3 - 2 * t)


def render_frame(frame: int, background: Image.Image, masks: list[Image.Image]) -> Image.Image:
    image = background.copy()
    draw = ImageDraw.Draw(image)
    word_index = frame // FRAMES_PER_WORD
    progress = slide_progress(frame)

    # The slim accent stays in the reading position while words move through it.
    draw.rounded_rectangle((CENTER - 42, 55, CENTER + 42, 57), radius=1, fill=(42, 121, 131))
    for offset in (-1, 0, 1, 2):
        index = (word_index + offset) % len(WORDS)
        mask = masks[index]
        x = CENTER + (offset - progress) * SPACING
        if x + mask.width / 2 < 0 or x - mask.width / 2 >= WIDTH:
            continue
        emphasis = max(0.0, 1.0 - abs(x - CENTER) / SPACING)
        color = tuple(round(a + (b - a) * emphasis) for a, b in zip(SIDE_COLOR, CENTER_COLOR))
        image.paste(color, (round(x - mask.width / 2), round((HEIGHT - mask.height) / 2) - 1), mask)
    return image


def encode(output: Path, font_path: Path) -> None:
    masks = text_masks(font_path)
    background = make_background()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp.mkv")
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s:v", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "-", "-frames:v", str(FRAMES), "-an",
        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact",
        "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", str(temporary),
    ]
    try:
        with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
            assert process.stdin is not None
            for frame in range(FRAMES):
                process.stdin.write(render_frame(frame, background, masks).tobytes())
            process.stdin.close()
            if process.wait() != 0:
                raise RuntimeError("ffmpeg failed to encode the showcase")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path.home() / ".local/share/touchbar-animations/linux-showcase.mkv")
    parser.add_argument("--font", type=Path, default=Path.home() / ".local/share/fonts/JetBrainsMonoNerdFont/JetBrainsMonoNerdFont-Bold.ttf")
    args = parser.parse_args()
    encode(args.output.expanduser(), args.font.expanduser())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

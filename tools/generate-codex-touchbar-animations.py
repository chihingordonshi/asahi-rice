#!/usr/bin/env python3
"""Generate deterministic Codex completion animations for the M1 Touch Bar."""

from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 2008
HEIGHT = 60
FPS = 30
FRAMES = 105


def background(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), top)
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
        draw.line((0, y, WIDTH, y), fill=color)
    return image


def train_frame(frame_number: int) -> Image.Image:
    image = background((7, 9, 22), (25, 20, 35))
    draw = ImageDraw.Draw(image)

    # A fixed night sky makes the motion easy to read on the very short panel.
    for i in range(58):
        x = (i * 337 + 71) % WIDTH
        y = 3 + (i * 17) % 30
        brightness = 105 + (i * 47) % 125
        draw.point((x, y), fill=(brightness, brightness, min(255, brightness + 24)))

    draw.ellipse((1518, 5, 1552, 39), fill=(238, 218, 157), outline=(255, 240, 195))
    draw.ellipse((1507, 0, 1541, 34), fill=(9, 11, 25))

    # Ballast, sleepers, and rails.
    draw.rectangle((0, 48, WIDTH, 59), fill=(31, 27, 34))
    for x in range(-20, WIDTH + 30, 42):
        draw.polygon(((x, 51), (x + 31, 51), (x + 37, 57), (x + 5, 57)), fill=(78, 53, 45))
    draw.rectangle((0, 49, WIDTH, 51), fill=(168, 157, 155))
    draw.line((0, 52, WIDTH, 52), fill=(61, 55, 62))

    progress = frame_number / (FRAMES - 1)
    engine_x = round(-120 + progress * (WIDTH + 1100))
    base_y = 43

    # Steam puffs drift upward and backward from the chimney.
    for puff in range(7):
        age = (frame_number - puff * 7) % 49
        if age > 34:
            continue
        px = engine_x + 35 - age * 5
        py = 11 - age * 0.32
        radius = 2 + age // 7
        shade = 158 - age * 2
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=(shade, shade, shade + 8))

    # Three passenger cars trail the locomotive.
    for car in range(3):
        right = engine_x - 80 - car * 245
        left = right - 220
        color = ((76, 72, 126), (106, 61, 91), (53, 91, 98))[car]
        draw.rounded_rectangle((left, 23, right, base_y), radius=4, fill=color, outline=(194, 168, 177), width=1)
        draw.rectangle((left + 11, 28, right - 10, 35), fill=(18, 21, 35))
        for window in range(5):
            wx = left + 18 + window * 38
            glow = (246, 192, 100) if (window + car) % 3 else (120, 187, 190)
            draw.rectangle((wx, 29, wx + 24, 34), fill=glow)
        draw.line((left + 4, 39, right - 4, 39), fill=(221, 178, 109))
        for wheel_x in (left + 42, right - 42):
            draw.ellipse((wheel_x - 7, 40, wheel_x + 7, 54), fill=(9, 10, 15), outline=(151, 138, 143))
            draw.ellipse((wheel_x - 2, 45, wheel_x + 2, 49), fill=(205, 187, 174))

    # Couplings.
    for coupling_x in (engine_x - 73, engine_x - 318, engine_x - 563):
        draw.rectangle((coupling_x - 8, 38, coupling_x + 8, 41), fill=(173, 148, 130))

    # Locomotive: warm brass highlights against a deep green body.
    draw.rounded_rectangle((engine_x - 70, 24, engine_x + 145, base_y), radius=6, fill=(31, 102, 88), outline=(180, 195, 157))
    draw.rectangle((engine_x - 67, 17, engine_x - 9, 42), fill=(37, 74, 73), outline=(188, 171, 122))
    draw.rectangle((engine_x - 57, 21, engine_x - 19, 31), fill=(244, 184, 92))
    draw.rectangle((engine_x - 3, 20, engine_x + 22, 27), fill=(184, 68, 52))
    draw.rectangle((engine_x + 2, 11, engine_x + 17, 22), fill=(46, 51, 61), outline=(188, 171, 122))
    draw.polygon(((engine_x - 5, 11), (engine_x + 24, 11), (engine_x + 18, 7), (engine_x + 1, 7)), fill=(54, 58, 67))
    draw.ellipse((engine_x + 125, 29, engine_x + 151, 42), fill=(42, 48, 51), outline=(188, 171, 122))
    draw.ellipse((engine_x + 139, 31, engine_x + 150, 39), fill=(255, 230, 142))
    draw.polygon(((engine_x + 143, 42), (engine_x + 169, 49), (engine_x + 128, 49)), fill=(154, 65, 55))
    for wheel_x, radius in ((engine_x - 43, 9), (engine_x + 38, 11), (engine_x + 102, 11)):
        draw.ellipse((wheel_x - radius, 38, wheel_x + radius, 38 + radius * 2), fill=(10, 12, 17), outline=(188, 162, 138), width=2)
        draw.ellipse((wheel_x - 3, 46, wheel_x + 3, 52), fill=(201, 183, 166))
    draw.line((engine_x + 31, 49, engine_x + 109, 49), fill=(218, 117, 78), width=2)
    return image


def _vine_y(x: float) -> float:
    return 30 + 8 * math.sin(x / 137) + 3 * math.sin(x / 47)


def vine_frame(frame_number: int) -> Image.Image:
    image = background((3, 15, 14), (7, 27, 22))
    draw = ImageDraw.Draw(image)
    progress = frame_number / (FRAMES - 1)
    # Leave a short final hold so the completed garden can be seen.
    reveal = min(1.0, progress / 0.86)
    reveal = reveal * reveal * (3 - 2 * reveal)
    tip_x = max(3, round(reveal * (WIDTH - 10)))

    points = [(x, round(_vine_y(x))) for x in range(0, tip_x + 1, 4)]
    if points[-1][0] != tip_x:
        points.append((tip_x, round(_vine_y(tip_x))))
    if len(points) > 1:
        draw.line(points, fill=(41, 126, 77), width=5, joint="curve")
        draw.line(points, fill=(87, 181, 104), width=2, joint="curve")

    branch_positions = list(range(95, WIDTH - 30, 105))
    for index, base_x in enumerate(branch_positions):
        local = (tip_x - base_x) / 70
        if local <= 0:
            continue
        local = min(1.0, local)
        base_y = _vine_y(base_x)
        direction = -1 if index % 2 == 0 else 1
        branch_len = (18 + index % 4 * 3) * local
        end_x = base_x + branch_len
        end_y = base_y + direction * (13 + index % 3 * 2) * local
        draw.line((base_x, base_y, end_x, end_y), fill=(59, 153, 84), width=2)

        if local > 0.30:
            leaf_scale = (local - 0.30) / 0.70
            leaf_w = 11 * leaf_scale
            leaf_h = 5 * leaf_scale
            color = ((64, 171, 95), (80, 190, 105), (48, 145, 88))[index % 3]
            draw.ellipse((end_x - leaf_w, end_y - leaf_h, end_x + leaf_w, end_y + leaf_h), fill=color, outline=(115, 210, 127))
            draw.line((end_x - leaf_w * 0.7, end_y, end_x + leaf_w * 0.7, end_y), fill=(29, 102, 65), width=1)

        if local > 0.78 and index % 5 == 2:
            flower = (local - 0.78) / 0.22
            radius = 4 * flower
            petals = (226, 130, 166) if index % 10 == 2 else (180, 143, 224)
            for angle in range(0, 360, 72):
                radians = math.radians(angle)
                cx = end_x + math.cos(radians) * radius
                cy = end_y + math.sin(radians) * radius
                draw.ellipse((cx - radius / 2, cy - radius / 2, cx + radius / 2, cy + radius / 2), fill=petals)
            draw.ellipse((end_x - 1.5, end_y - 1.5, end_x + 1.5, end_y + 1.5), fill=(247, 211, 103))

    # The bright growing tip communicates direction without any text.
    tip_y = _vine_y(tip_x)
    draw.ellipse((tip_x - 6, tip_y - 6, tip_x + 6, tip_y + 6), fill=(33, 83, 55))
    draw.ellipse((tip_x - 3, tip_y - 3, tip_x + 3, tip_y + 3), fill=(151, 229, 130))
    return image


def encode(output: Path, renderer) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s:v", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "-", "-frames:v", str(FRAMES), "-an",
        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact",
        "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for frame_number in range(FRAMES):
            process.stdin.write(renderer(frame_number).tobytes())
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise SystemExit(f"ffmpeg failed while writing {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_output = Path(__file__).resolve().parents[1] / ".local/share/touchbar-animations"
    parser.add_argument("--output-dir", type=Path, default=default_output)
    args = parser.parse_args()
    encode(args.output_dir / "codex-train.mkv", train_frame)
    encode(args.output_dir / "codex-vines.mkv", vine_frame)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

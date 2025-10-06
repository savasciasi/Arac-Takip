"""Runtime theme builder that converts tokens into QSS."""

from __future__ import annotations

import json
from pathlib import Path
from string import Template

BASE_FONT_SIZE = 14

TEMPLATE = Template(
    """
/* Generated theme */
QWidget {
    background: $bg;
    color: $text;
    font-family: "Segoe UI", "Helvetica Neue", Arial;
    font-size: $font_size;
}

QFrame#Card, QWidget#Card {
    background: $card;
    border-radius: $radius_md;
    border: 1px solid rgba(15, 23, 42, 0.05);
    box-shadow: $shadow_sm;
}

QFrame#Sidebar {
    background: $card;
    border-radius: $radius_xl;
    border: 1px solid rgba(15, 23, 42, 0.08);
    padding: $space_8;
}

QPushButton {
    border-radius: $radius_md;
    padding: $space_4 $space_8;
    background: transparent;
    border: 1px solid rgba(15, 23, 42, 0.08);
    transition: all 160ms ease;
}

QPushButton[nav="true"] {
    border: none;
    padding: $space_4 $space_8;
    background: transparent;
    text-align: left;
    font-weight: 500;
}

QPushButton[variant="primary"] {
    background: $accent_primary;
    color: #fff;
    border: none;
}

QPushButton[variant="secondary"] {
    background: $accent_secondary;
    color: #fff;
    border: none;
}

QPushButton[variant="destructive"] {
    background: $accent_destructive;
    color: #fff;
    border: none;
}

QPushButton:hover {
    background-color: rgba(255,255,255,$hover);
}

QPushButton[nav="true"]:hover {
    background: rgba(47, 128, 237, 0.12);
}

QPushButton:pressed {
    transform: translateY(1px);
    opacity: 0.9;
}

QPushButton:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(47, 128, 237, $focus);
}

QPushButton[nav="true"]:checked {
    background: $accent_primary;
    color: #fff;
}

QLineEdit, QDateEdit, QTextEdit, QComboBox {
    background: $card;
    border-radius: $radius_md;
    border: 1px solid rgba(15, 23, 42, 0.12);
    padding: $space_4;
}

QLabel[role="page-title"] {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: $space_4;
}

QLabel[role="card-title"] {
    font-size: 18px;
    font-weight: 600;
}

QLabel[role="muted"] {
    color: $muted;
}

QTableView {
    background: $card;
    border-radius: $radius_md;
    border: 1px solid rgba(15, 23, 42, 0.06);
    gridline-color: rgba(15, 23, 42, 0.08);
    selection-background-color: rgba(47, 128, 237, 0.12);
}

QHeaderView::section {
    background: rgba(15, 23, 42, 0.04);
    border: none;
    padding: $space_2;
}

QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: $space_2 0 $space_2 0;
}

QScrollBar::handle:vertical {
    background: rgba(15, 23, 42, 0.25);
    border-radius: $space_2;
}
"""
)


def _load_tokens() -> dict[str, dict[str, dict[str, object]]]:
    token_path = Path(__file__).with_name("theme.tokens.json")
    data = json.loads(token_path.read_text(encoding="utf-8"))
    return data.get("profiles", {})


def generate(profile: str, theme: str = "light", text_scale: float = 1.0, output: Path | None = None) -> str:
    """Generate QSS string for a given profile and optionally save it."""

    profiles = _load_tokens()
    profile_tokens = profiles.get(profile)
    if not profile_tokens:
        raise KeyError(f"Unknown profile: {profile}")

    theme_tokens = profile_tokens.get(theme)
    if not theme_tokens:
        raise KeyError(f"Profile '{profile}' does not define theme '{theme}'")

    accent = theme_tokens["color"]["accent"]
    font_px = f"{int(round(BASE_FONT_SIZE * max(text_scale, 0.5)))}px"
    mapping = {
        "bg": theme_tokens["color"]["bg"],
        "card": theme_tokens["color"]["card"],
        "text": theme_tokens["color"]["text"],
        "muted": theme_tokens["color"].get("muted", "#6b7280"),
        "radius_md": theme_tokens["radius"]["md"],
        "radius_xl": theme_tokens["radius"]["xl"],
        "shadow_sm": theme_tokens["shadow"]["sm"],
        "shadow_lg": theme_tokens["shadow"]["lg"],
        "space_2": theme_tokens["space"]["2"],
        "space_4": theme_tokens["space"]["4"],
        "space_8": theme_tokens["space"]["8"],
        "accent_primary": accent["primary"],
        "accent_secondary": accent["secondary"],
        "accent_destructive": accent["destructive"],
        "focus": theme_tokens["opacity"]["focus"],
        "hover": theme_tokens["opacity"]["hover"],
        "font_size": font_px,
    }

    qss = TEMPLATE.substitute(mapping)
    token_path = Path(__file__).with_name("theme.tokens.json")
    out_path = output or token_path.with_name("theme.qss")
    out_path.write_text(qss, encoding="utf-8")
    return qss


if __name__ == "__main__":
    generate("minimal")

"""Runtime QSS builder that maps design tokens to themed style sheets."""
import json
from pathlib import Path
from string import Template

TEMPLATE = Template(
    """
/* Generated theme */
QWidget {
    background: $bg;
    color: $text;
    font-family: "Segoe UI", "Helvetica Neue", Arial;
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
    color: rgba(29, 31, 36, 0.65);
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


def generate(profile: str, output: Path | None = None) -> str:
    """Generate QSS string for a given profile and optionally save it."""
    token_path = Path(__file__).with_name("theme.tokens.json")
    data = json.loads(token_path.read_text(encoding="utf-8"))
    profiles = data.get("profiles", {})
    if profile not in profiles:
        raise KeyError(f"Unknown profile: {profile}")

    tokens = profiles[profile]
    accent = tokens["color"]["accent"]
    mapping = {
        "bg": tokens["color"]["bg"],
        "card": tokens["color"]["card"],
        "text": tokens["color"]["text"],
        "radius_md": tokens["radius"]["md"],
        "radius_xl": tokens["radius"]["xl"],
        "shadow_sm": tokens["shadow"]["sm"],
        "shadow_lg": tokens["shadow"]["lg"],
        "space_2": tokens["space"]["2"],
        "space_4": tokens["space"]["4"],
        "space_8": tokens["space"]["8"],
        "accent_primary": accent["primary"],
        "accent_secondary": accent["secondary"],
        "accent_destructive": accent["destructive"],
        "focus": tokens["opacity"]["focus"],
        "hover": tokens["opacity"]["hover"],
    }

    qss = TEMPLATE.substitute(mapping)
    out_path = output or token_path.with_name("theme.qss")
    out_path.write_text(qss, encoding="utf-8")
    return qss


if __name__ == "__main__":
    generate("minimal")

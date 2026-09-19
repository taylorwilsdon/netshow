"""The original Selenized palette, registered as a switchable Textual theme."""

from textual.theme import Theme

SELENIZED_DARK = Theme(
    name="selenized-dark",
    primary="#4191a5",
    secondary="#58a3ff",
    success="#75b938",
    warning="#dbb32d",
    error="#fa5750",
    accent="#f275be",
    background="#103c48",
    surface="#184956",
    panel="#184956",
    foreground="#adbcbc",
    variables={
        "text": "#cad8d9",
        "text-muted": "#72898f",
        "block-cursor-background": "#2d5b69",
        "block-cursor-foreground": "#cad8d9",
        "block-cursor-text-style": "bold",
        "block-cursor-blurred-background": "#184956",
        "block-cursor-blurred-foreground": "#cad8d9",
        "block-hover-background": "#184956",
        "footer-background": "#184956",
        "footer-key-foreground": "#53d6c7",
        "footer-description-foreground": "#cad8d9",
        "input-selection-background": "#2d5b69",
    },
)

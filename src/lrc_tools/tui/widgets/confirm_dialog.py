"""Confirmation dialog modal screen."""

from textual import on
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmDialog(ModalScreen[bool]):
    DEFAULT_CSS = """
    ConfirmDialog { align: center middle; }
    """

    def __init__(self, message: str, *, default_yes: bool = True) -> None:
        super().__init__()
        self.message = message
        self.default_yes = default_yes

    def compose(self):
        with Container(id="dialog"):
            yield Static(self.message)
            with Horizontal(id="dialog-buttons"):
                yield Button("S\u00ed (Y)", id="yes", variant="success")
                yield Button("No (N)", id="no", variant="default")

    def on_mount(self) -> None:
        self.call_after_refresh(self._focus_default)

    def _focus_default(self) -> None:
        btn_id = "yes" if self.default_yes else "no"
        self.query_one(f"#{btn_id}", Button).focus()

    @on(Button.Pressed, "#yes")
    def yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def no(self) -> None:
        self.dismiss(False)

    def key_y(self) -> None:
        self.dismiss(True)

    def key_n(self) -> None:
        self.dismiss(False)

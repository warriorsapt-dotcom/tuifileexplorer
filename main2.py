from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree, Static
from textual.containers import Horizontal
from textual import events
import os

class FilePreview(Static):
    """Displays file content or info."""

    def show_file(self, path: str):
        self.update("")  # clear previous content
        if os.path.isdir(path):
            self.update(f"[b cyan]📁 {path}[/b cyan]\n\nThis is a directory.")
            return

        try:
            with open(path, "r") as f:
                content = f.read(1500)  # limit preview to avoid huge files
            self.update(f"[b green]{path}[/b green]\n\n{content}")
        except Exception as e:
            self.update(f"[b red]Error:[/b red] {e}")

class StatusBar(Static):
    """Shows current path and info."""
    def update_status(self, path: str):
        self.update(f"[b yellow]Current:[/b yellow] {path}")

class FileExplorer(App):
    """Main TUI file explorer with keybindings."""
    BINDINGS = [
        ("q", "quit_app", "Quit"),
        ("r", "refresh_tree", "Refresh"),
        ("h", "focus_tree", "Focus Tree"),
        ("l", "focus_preview", "Focus Preview"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            self.dir_tree = DirectoryTree(".")
            self.preview = FilePreview("Select a file to preview")
            yield self.dir_tree
            yield self.preview
        self.status = StatusBar()
        yield self.status
        yield Footer()

    async def on_mount(self):
        self.dir_tree.focus()
        self.status.update_status(os.getcwd())

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ):
        """When a file is selected, show its contents."""
        self.preview.show_file(event.path)
        self.status.update_status(event.path)

    async def action_quit_app(self):
        await self.action_quit()

    async def action_refresh_tree(self):
        """Refresh directory tree."""
        path = self.dir_tree.path
        self.dir_tree.path = path  # reload same dir
        self.status.update_status(f"Refreshed: {path}")

    async def action_focus_tree(self):
        self.dir_tree.focus()
        self.status.update_status("Focus: Directory Tree")

    async def action_focus_preview(self):
        self.preview.focus()
        self.status.update_status("Focus: Preview Panel")

if __name__ == "__main__":
    FileExplorer().run()

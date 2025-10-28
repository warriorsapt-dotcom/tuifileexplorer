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
                content = f.read(1000)  # limit preview to 1000 chars
            self.update(f"[b green]{path}[/b green]\n\n{content}")
        except Exception as e:
            self.update(f"[b red]Error:[/b red] {e}")

class FileExplorer(App):
    """Main file explorer app."""
    CSS_PATH = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            self.tree = DirectoryTree(".")
            self.preview = FilePreview("Select a file to preview")
            yield self.tree
            yield self.preview
        yield Footer()

    async def on_mount(self):
        self.tree.focus()

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ):
        """When a file is selected, show its contents."""
        self.preview.show_file(event.path)

if __name__ == "__main__":
    FileExplorer().run()

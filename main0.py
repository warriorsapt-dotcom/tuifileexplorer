from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree, Static

class FileExplorer(App):
    CSS_PATH = None  # we’ll add custom styling later

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DirectoryTree(".")
        yield Footer()

if __name__ == "__main__":
    FileExplorer().run()

import platform
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree, Static, Input, ListView, ListItem
from textual.containers import Horizontal, Vertical
import os
import subprocess
import shutil

class FilePreview(Static):
    """Displays file content or info."""

    def show_file(self, path: str):
        self.update("")
        if os.path.isdir(path):
            self.update(f"[b cyan]📁 {path}[/b cyan]\n\nThis is a directory.")
            return
        try:
            with open(path, "r", encoding='utf-8', errors='ignore') as f:
                content = f.read(1500)
            self.update(f"[b green]{path}[/b green]\n\n{content}")
        except Exception as e:
            self.update(f"[b red]Error:[/b red] {e}")

class StatusBar(Static):
    """Shows current path and info."""
    def update_status(self, msg: str):
        self.update(f"[b yellow]{msg}[/b yellow]")

class CommandSuggestions(ListView):
    """Popup suggestion list for command input."""
    def show_suggestions(self, suggestions):
        self.clear()
        for s in suggestions:
            self.append(ListItem(Static(s)))
        self.display = bool(suggestions)

class FileExplorer(App):
    """TUI file explorer with command bar & autocompletion."""
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("q", "quit_app", "Quit"),
        (":", "enter_command_mode", "Command Mode"),
        ("escape", "exit_command_mode", "Exit Command Mode"),
    ]

    COMMANDS = ["open", "delete", "rename", "refresh", "quit", "exit"]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Horizontal():
                self.dir_tree = DirectoryTree(os.getcwd())
                self.preview = FilePreview("Select a file to preview")
                yield self.dir_tree
                yield self.preview
            self.status = StatusBar()
            yield self.status
            self.command_input = Input(placeholder="Type command and press Enter...", id="cmdbar")
            self.command_input.display = False
            yield self.command_input
            self.suggestions = CommandSuggestions(id="suggestions")
            self.suggestions.display = False
            yield self.suggestions
        yield Footer()

    async def on_mount(self):
        self.dir_tree.focus()
        self.status.update_status("Ready. Press ':' for command mode.")

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ):
        """When a file is selected, show its contents."""
        self.current_path = event.path
        self.preview.show_file(event.path)
        self.status.update_status(f"Selected: {event.path}")

    async def action_quit_app(self):
        await self.action_quit()

    async def action_enter_command_mode(self):
        """Activate the command bar."""
        self.command_input.display = True
        self.command_input.focus()
        self.command_input.value = ""
        self.suggestions.display = False
        self.status.update_status("Command mode: Type a command and press Enter. Press ESC to cancel.")

    async def action_exit_command_mode(self):
        """Exit command mode without executing."""
        if self.command_input.display:
            self.command_input.display = False
            self.suggestions.display = False
            self.dir_tree.focus()
            self.status.update_status("Command cancelled.")

    async def on_input_changed(self, event: Input.Changed):
        """Show command suggestions as user types."""
        # Only handle changes from the command input
        if event.input.id != "cmdbar":
            return
            
        value = event.value.strip()
        if not value:
            self.suggestions.display = False
            return

        matches = [cmd for cmd in self.COMMANDS if cmd.startswith(value)]
        self.suggestions.show_suggestions(matches)

    async def on_input_submitted(self, message: Input.Submitted):
        """Handle commands entered in command bar."""
        # Only handle submissions from the command input
        if message.input.id != "cmdbar":
            return
            
        cmd = message.value.strip()
        
        # Clear the input but keep it visible until we process the command
        self.command_input.value = ""
        self.suggestions.display = False

        if not cmd:
            self.command_input.display = False
            self.dir_tree.focus()
            return

        parts = cmd.split()
        main_cmd = parts[0]
        args = parts[1:]

        try:
            if main_cmd in ["q", "quit", "exit"]:
                await self.action_quit_app()
            elif main_cmd in ["open", "o"]:
                await self.open_selected_file()
            elif main_cmd in ["delete", "rm"]:
                await self.delete_selected_file()
            elif main_cmd in ["rename", "mv"] and args:
                await self.rename_selected_file(args[0])
            elif main_cmd in ["refresh", "r"]:
                await self.refresh_tree()
            else:
                self.status.update_status(f"Unknown command: {cmd}")
        except Exception as e:
            self.status.update_status(f"Error: {e}")
        finally:
            # Hide command input after command execution
            self.command_input.display = False
            self.dir_tree.focus()

    async def open_selected_file(self):
        if not hasattr(self, "current_path"):
            self.status.update_status("No file selected.")
            return
        path = self.current_path
        if os.path.isdir(path):
            self.status.update_status("Can't open directories yet.")
            return
        
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":
                subprocess.run(["open", path], check=False)
            else:  # Linux and other Unix-like
                subprocess.run(["xdg-open", path], check=False)
            self.status.update_status(f"Opened: {path}")
        except Exception as e:
            self.status.update_status(f"Error opening file: {e}")

    async def delete_selected_file(self):
        if not hasattr(self, "current_path"):
            self.status.update_status("No file selected.")
            return
        path = self.current_path
        if not os.path.exists(path):
            self.status.update_status("File no longer exists.")
            return
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.status.update_status(f"Deleted: {path}")
            await self.refresh_tree()
        except Exception as e:
            self.status.update_status(f"Error deleting: {e}")

    async def rename_selected_file(self, new_name: str):
        if not hasattr(self, "current_path"):
            self.status.update_status("No file selected.")
            return
        old_path = self.current_path
        dir_path = os.path.dirname(old_path)
        new_path = os.path.join(dir_path, new_name)
        try:
            os.rename(old_path, new_path)
            self.status.update_status(f"Renamed to: {new_name}")
            await self.refresh_tree()
        except Exception as e:
            self.status.update_status(f"Rename failed: {e}")

    async def refresh_tree(self):
        path = self.dir_tree.path
        self.dir_tree.path = path
        self.status.update_status(f"Refreshed: {path}")

if __name__ == "__main__":
    FileExplorer().run()
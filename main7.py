import platform
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree, Static, Input, ListView, ListItem, Button, RichLog, Label
from textual.containers import Horizontal, Vertical, Container
from textual.reactive import reactive
from textual.binding import Binding
import os
import subprocess
import shutil
import stat
from pathlib import Path
from datetime import datetime

class FilePreview(Static):
    """Displays file content or info."""

    def show_file(self, path: str):
        self.update("")
        if os.path.isdir(path):
            # Show directory info
            try:
                items = os.listdir(path)
                file_count = len([f for f in items if os.path.isfile(os.path.join(path, f))])
                dir_count = len([f for f in items if os.path.isdir(os.path.join(path, f))])
                stat_info = os.stat(path)
                mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                self.update(f"""[b cyan]📁 {path}[/b cyan]

Files: {file_count}
Directories: {dir_count}
Total items: {len(items)}
Modified: {mod_time}
Size: {self.get_size(path)}""")
            except Exception as e:
                self.update(f"[b red]Error reading directory:[/b red] {e}")
            return
        
        # Show file info and content
        try:
            stat_info = os.stat(path)
            size = stat_info.st_size
            mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            file_info = f"""📄 [b green]{path}[/b green]

Size: {self.format_size(size)}
Modified: {mod_time}
Permissions: {self.get_permissions(stat_info.st_mode)}
Type: {self.get_file_type(path)}
"""
            
            # Try to read text files
            if size < 100000:  # Only read files smaller than 100KB
                try:
                    with open(path, "r", encoding='utf-8', errors='ignore') as f:
                        content = f.read(2000)
                        if len(content) == 2000:
                            content += "\n[...truncated...]"
                    file_info += f"\n--- Content ---\n{content}"
                except:
                    file_info += f"\n--- Binary file or encoding issue ---\n"
            else:
                file_info += f"\n--- File too large to preview ---\n"
            
            self.update(file_info)
        except Exception as e:
            self.update(f"[b red]Error:[/b red] {e}")

    def get_size(self, path: str) -> str:
        """Calculate directory size recursively."""
        try:
            if os.path.isfile(path):
                return self.format_size(os.path.getsize(path))
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
            return self.format_size(total)
        except:
            return "Unknown"

    def format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_permissions(self, mode: int) -> str:
        """Get file permissions in rwx format."""
        perm = ""
        for who in "USR", "GRP", "OTH":
            for what in "R", "W", "X":
                if mode & getattr(stat, f"S_I{what}{who}"):
                    perm += what.lower()
                else:
                    perm += "-"
        return perm

    def get_file_type(self, path: str) -> str:
        """Get file type/extension."""
        if os.path.isdir(path):
            return "Directory"
        ext = os.path.splitext(path)[1].lower()
        if ext:
            return f"File ({ext})"
        return "File"

class StatusBar(Static):
    """Shows current path and info."""
    current_path = reactive("")
    
    def update_status(self, msg: str):
        self.update(f"[b yellow]{msg}[/b yellow]")

class CommandSuggestions(ListView):
    """Popup suggestion list for command input."""
    def show_suggestions(self, suggestions):
        self.clear()
        for s in suggestions:
            self.append(ListItem(Static(s)))
        self.display = bool(suggestions)

class HelpPanel(Static):
    """Help panel showing available commands."""
    
    HELP_TEXT = """
[b cyan]📁 File Explorer Commands[/b cyan]

[b yellow]Navigation:[/b yellow]
  cd [path]      - Change directory
  pwd           - Show current directory
  refresh / r   - Refresh current view
  back / b      - Go to parent directory

[b yellow]File Operations:[/b yellow]
  open [file]   - Open file with default app
  edit [file]   - Edit file (uses $EDITOR or nano/vim)
  view [file]   - View file in preview panel
  touch [file]  - Create new file
  mkdir [dir]   - Create new directory

[b yellow]File Management:[/b yellow]
  copy / cp [src] [dest] - Copy file/directory
  move / mv [src] [dest] - Move file/directory  
  rename / rn [old] [new] - Rename file/directory
  delete / rm [path]     - Delete file/directory
  chmod [mode] [file]   - Change file permissions

[b yellow]Information:[/b yellow]
  ls [path]     - List directory contents
  stat [file]   - Show file/directory info
  find [name]   - Search for files
  tree [path]   - Show directory tree

[b yellow]System:[/b yellow]
  help          - Show this help
  clear         - Clear the screen
  quit / q / exit - Quit application

[b yellow]Shortcuts:[/b yellow]
  :             - Enter command mode
  Tab           - Auto-complete commands
  Esc           - Cancel command mode
  q             - Quit application
"""

    def show_help(self):
        self.update(self.HELP_TEXT)

class FileExplorer(App):
    """TUI file explorer with comprehensive file operations."""
    CSS_PATH = "app.tcss"
    
    # Disable the built-in command palette to avoid conflicts
    ENABLE_COMMAND_PALETTE = False
    
    BINDINGS = [
        ("q", "quit_app", "Quit"),
        (":", "enter_command_mode", "Command Mode"),
        ("escape", "exit_command_mode", "Exit Command Mode"),
        ("h", "show_help", "Help"),
        ("r", "refresh_tree", "Refresh"),
        ("backspace", "go_parent", "Parent Dir"),
    ]

    # Available commands for autocomplete
    MY_COMMANDS = [
        # Navigation
        "cd", "pwd", "refresh", "back", "ls", "tree",
        # File Operations
        "open", "edit", "view", "touch", "mkdir",
        # File Management
        "copy", "cp", "move", "mv", "rename", "rn", "delete", "rm", "chmod",
        # Information
        "stat", "find", "info",
        # System
        "help", "clear", "quit", "exit"
    ]

    def __init__(self):
        super().__init__()
        self.clipboard_buffer = None  # For copy/paste operations (avoid App.clipboard property)
        self.current_directory = os.getcwd()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Horizontal():
                self.dir_tree = DirectoryTree(self.current_directory)
                with Vertical():
                    self.preview = FilePreview("Select a file to preview")
                    self.help_panel = HelpPanel()
                    self.help_panel.display = False
                    yield self.preview
                    yield self.help_panel
                yield self.dir_tree
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
        self.status.update_status(f"Ready. Press ':' for command mode, 'h' for help. Current dir: {self.current_directory}")

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
        self.help_panel.display = False
        self.status.update_status("Command mode: Type a command and press Enter. Press ESC to cancel.")

    async def action_exit_command_mode(self):
        """Exit command mode without executing."""
        if self.command_input.display:
            self.command_input.display = False
            self.suggestions.display = False
            self.dir_tree.focus()
            self.status.update_status("Command cancelled.")

    async def action_show_help(self):
        """Toggle help panel."""
        if self.help_panel.display:
            self.help_panel.display = False
            self.dir_tree.focus()
        else:
            self.help_panel.display = True
            self.help_panel.show_help()
            self.status.update_status("Help: Press 'h' to close help.")

    async def action_refresh_tree(self):
        """Refresh directory tree."""
        await self.refresh_tree()

    async def action_go_parent(self):
        """Go to parent directory."""
        parent = os.path.dirname(self.current_directory)
        if parent != self.current_directory:
            self.current_directory = parent
            self.dir_tree.path = parent
            self.status.update_status(f"Changed to parent directory: {parent}")

    async def on_input_changed(self, event: Input.Changed):
        """Show command suggestions as user types."""
        if event.input.id != "cmdbar":
            return
            
        value = event.value.strip()
        if not value:
            self.suggestions.display = False
            return

        matches = [cmd for cmd in self.MY_COMMANDS if cmd.startswith(value)]
        self.suggestions.show_suggestions(matches[:8])  # Limit to 8 suggestions

    async def on_input_submitted(self, message: Input.Submitted):
        """Handle commands entered in command bar."""
        if message.input.id != "cmdbar":
            return
            
        cmd = message.value.strip()
        self.command_input.value = ""
        self.suggestions.display = False

        if not cmd:
            self.command_input.display = False
            self.dir_tree.focus()
            return

        parts = cmd.split()
        main_cmd = parts[0].lower()
        args = parts[1:]

        try:
            # Navigation commands
            if main_cmd in ["cd"]:
                await self.change_directory(args[0] if args else "~")
            elif main_cmd in ["pwd"]:
                self.status.update_status(f"Current directory: {self.current_directory}")
            elif main_cmd in ["back", "b"]:
                await self.action_go_parent()
            elif main_cmd in ["ls"]:
                await self.list_directory(args[0] if args else ".")
            elif main_cmd in ["tree"]:
                await self.show_tree(args[0] if args else ".")
            
            # File operations
            elif main_cmd in ["open", "o"]:
                await self.open_file(args[0] if args else self.current_path)
            elif main_cmd in ["edit"]:
                await self.edit_file(args[0] if args else self.current_path)
            elif main_cmd in ["view"]:
                await self.view_file(args[0] if args else self.current_path)
            elif main_cmd in ["touch"] and args:
                await self.create_file(args[0])
            elif main_cmd in ["mkdir"] and args:
                await self.create_directory(args[0])
            
            # File management
            elif main_cmd in ["copy", "cp"] and args:
                await self.copy_file(args[0], args[1] if len(args) > 1 else None)
            elif main_cmd in ["move", "mv"] and args:
                await self.move_file(args[0], args[1] if len(args) > 1 else None)
            elif main_cmd in ["rename", "rn"] and len(args) >= 2:
                await self.rename_file(args[0], args[1])
            elif main_cmd in ["delete", "rm"] and args:
                await self.delete_path(args[0])
            elif main_cmd in ["chmod"] and len(args) >= 2:
                await self.change_permissions(args[0], args[1])
            
            # Information commands
            elif main_cmd in ["stat", "info"] and args:
                await self.show_file_info(args[0])
            elif main_cmd in ["find"] and args:
                await self.find_files(args[0], args[1] if len(args) > 1 else ".")
            
            # System commands
            elif main_cmd in ["help"]:
                await self.action_show_help()
            elif main_cmd in ["clear"]:
                self.preview.update("")
                self.status.update_status("Screen cleared.")
            elif main_cmd in ["q", "quit", "exit"]:
                await self.action_quit_app()
            elif main_cmd in ["refresh", "r"]:
                await self.refresh_tree()
            else:
                self.status.update_status(f"Unknown command: {cmd}. Type 'help' for available commands.")
        except Exception as e:
            self.status.update_status(f"Error executing '{cmd}': {e}")
        finally:
            self.command_input.display = False
            self.dir_tree.focus()

    # Navigation methods
    async def change_directory(self, path: str):
        """Change current directory."""
        if path == "~":
            path = os.path.expanduser("~")
        elif not os.path.isabs(path):
            path = os.path.join(self.current_directory, path)
        
        if os.path.isdir(path):
            self.current_directory = path
            self.dir_tree.path = path
            self.status.update_status(f"Changed to: {path}")
        else:
            self.status.update_status(f"Directory not found: {path}")

    async def list_directory(self, path: str):
        """List directory contents."""
        if not os.path.isabs(path):
            path = os.path.join(self.current_directory, path)
        
        if os.path.exists(path):
            try:
                items = os.listdir(path)
                dirs = [f"📁 {d}" for d in items if os.path.isdir(os.path.join(path, d))]
                files = [f"📄 {f}" for f in items if os.path.isfile(os.path.join(path, f))]
                output = "\n".join(sorted(dirs) + sorted(files))
                self.preview.update(f"[b cyan]Contents of {path}:[/b cyan]\n\n{output}")
            except Exception as e:
                self.status.update_status(f"Error listing directory: {e}")
        else:
            self.status.update_status(f"Path not found: {path}")

    async def show_tree(self, path: str):
        """Show directory tree."""
        if not os.path.isabs(path):
            path = os.path.join(self.current_directory, path)
        
        try:
            tree_output = self.generate_tree(path, max_depth=3)
            self.preview.update(f"[b cyan]Directory tree for {path}:[/b cyan]\n\n{tree_output}")
        except Exception as e:
            self.status.update_status(f"Error generating tree: {e}")

    def generate_tree(self, path: str, prefix: str = "", max_depth: int = 3, depth: int = 0) -> str:
        """Generate directory tree string."""
        if depth > max_depth:
            return prefix + "└── ...\n"
        
        name = os.path.basename(path) or path
        result = prefix + "└── " + name + "\n"
        
        if os.path.isdir(path):
            try:
                items = sorted(os.listdir(path))
                for i, item in enumerate(items):
                    item_path = os.path.join(path, item)
                    is_last = i == len(items) - 1
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    result += self.generate_tree(item_path, new_prefix, max_depth, depth + 1)
            except PermissionError:
                result += prefix + "    └── [Permission denied]\n"
        
        return result

    # File operation methods
    async def open_file(self, path: str):
        """Open file with default application."""
        if not os.path.exists(path):
            self.status.update_status(f"File not found: {path}")
            return
        
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
            self.status.update_status(f"Opened: {path}")
        except Exception as e:
            self.status.update_status(f"Error opening file: {e}")

    async def edit_file(self, path: str):
        """Edit file with system editor."""
        if not os.path.exists(path):
            self.status.update_status(f"File not found: {path}")
            return
        
        editor = os.environ.get('EDITOR', 'nano' if shutil.which('nano') else 'vi')
        try:
            subprocess.run([editor, path])
            self.status.update_status(f"Edited: {path}")
            self.preview.show_file(path)  # Refresh preview
        except Exception as e:
            self.status.update_status(f"Error editing file: {e}")

    async def view_file(self, path: str):
        """View file in preview panel."""
        if os.path.exists(path):
            self.preview.show_file(path)
            self.status.update_status(f"Viewing: {path}")
        else:
            self.status.update_status(f"File not found: {path}")

    async def create_file(self, filename: str):
        """Create a new file."""
        if not os.path.isabs(filename):
            filename = os.path.join(self.current_directory, filename)
        
        try:
            with open(filename, 'a'):
                os.utime(filename, None)
            self.status.update_status(f"Created file: {filename}")
            await self.refresh_tree()
        except Exception as e:
            self.status.update_status(f"Error creating file: {e}")

    async def create_directory(self, dirname: str):
        """Create a new directory."""
        if not os.path.isabs(dirname):
            dirname = os.path.join(self.current_directory, dirname)
        
        try:
            os.makedirs(dirname, exist_ok=True)
            self.status.update_status(f"Created directory: {dirname}")
            await self.refresh_tree()
        except Exception as e:
            self.status.update_status(f"Error creating directory: {e}")

    # File management methods
    async def copy_file(self, src: str, dest: str = None):
        """Copy file or directory."""
        if not os.path.isabs(src):
            src = os.path.join(self.current_directory, src)
        
        if dest is None:
            dest = self.current_directory
        elif not os.path.isabs(dest):
            dest = os.path.join(self.current_directory, dest)
        
        try:
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(dest, os.path.basename(src)))
            else:
                shutil.copy2(src, dest)
            self.status.update_status(f"Copied: {src} → {dest}")
            await self.refresh_tree()
        except Exception as e:
            self.status.update_status(f"Error copying: {e}")

    async def move_file(self, src: str, dest: str = None):
        """Move file or directory."""
        if not os.path.isabs(src):
            src = os.path.join(self.current_directory, src)
        
        if dest is None:
            dest = self.current_directory
        elif not os.path.isabs(dest):
            dest = os.path.join(self.current_directory, dest)
        
        try:
            shutil.move(src, dest)
            self.status.update_status(f"Moved: {src} → {dest}")
            await self.refresh_tree()
        except Exception as e:
            self.status.update_status(f"Error moving: {e}")

    async def rename_file(self, old_name: str, new_name: str):
        """Rename file or directory."""
        if not os.path.isabs(old_name):
            old_name = os.path.join(self.current_directory, old_name)
        
        if not os.path.isabs(new_name):
            new_name = os.path.join(self.current_directory, new_name)
        
        try:
            os.rename(old_name, new_name)
            self.status.update_status(f"Renamed: {old_name} → {new_name}")
            await self.refresh_tree()
        except Exception as e:
            self.status.update_status(f"Error renaming: {e}")

    async def delete_path(self, path: str):
        """Delete file or directory."""
        if not os.path.isabs(path):
            path = os.path.join(self.current_directory, path)
        
        if not os.path.exists(path):
            self.status.update_status(f"Path not found: {path}")
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

    async def change_permissions(self, mode: str, path: str):
        """Change file permissions."""
        if not os.path.isabs(path):
            path = os.path.join(self.current_directory, path)
        
        try:
            # Convert octal string to integer
            octal_mode = int(mode, 8)
            os.chmod(path, octal_mode)
            self.status.update_status(f"Changed permissions of {path} to {mode}")
        except Exception as e:
            self.status.update_status(f"Error changing permissions: {e}")

    # Information methods
    async def show_file_info(self, path: str):
        """Show detailed file information."""
        if not os.path.isabs(path):
            path = os.path.join(self.current_directory, path)
        
        if os.path.exists(path):
            self.preview.show_file(path)
            self.status.update_status(f"Showing info for: {path}")
        else:
            self.status.update_status(f"File not found: {path}")

    async def find_files(self, pattern: str, search_dir: str = "."):
        """Find files matching pattern."""
        if not os.path.isabs(search_dir):
            search_dir = os.path.join(self.current_directory, search_dir)
        
        try:
            matches = []
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if pattern.lower() in file.lower():
                        matches.append(os.path.join(root, file))
                # Also check directory names
                for dir in dirs:
                    if pattern.lower() in dir.lower():
                        matches.append(os.path.join(root, dir))
            
            if matches:
                result = "\n".join(matches[:20])  # Limit to 20 results
                if len(matches) > 20:
                    result += f"\n\n... and {len(matches) - 20} more matches"
                self.preview.update(f"[b cyan]Found {len(matches)} matches for '{pattern}':[/b cyan]\n\n{result}")
            else:
                self.preview.update(f"[b yellow]No matches found for '{pattern}' in {search_dir}[/b yellow]")
        except Exception as e:
            self.status.update_status(f"Error searching: {e}")

    async def refresh_tree(self):
        """Refresh directory tree."""
        self.dir_tree.path = self.current_directory
        self.status.update_status(f"Refreshed: {self.current_directory}")

if __name__ == "__main__":
    FileExplorer().run()
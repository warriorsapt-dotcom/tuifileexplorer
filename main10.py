import os
import platform
import subprocess
import shutil
import stat
import glob
from pathlib import Path
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    DirectoryTree,
    Static,
    Input,
    ListView,
    ListItem,
)
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual import events
from textual.reactive import reactive

HELP_TEXT = """
[b cyan]📁 TUI File Explorer - Complete Command Reference[/b cyan]

[b yellow]🎯 BASIC NAVIGATION[/b yellow]
  [green]cd [directory][/green]         - Change current directory
  [green]pwd[/green]                    - Print working directory
  [green]back / b[/green]               - Go to parent directory
  [green]refresh / r[/green]            - Refresh directory view

[b yellow]📋 FILE LISTING & VIEWING[/b yellow]
  [green]ls [path][/green]              - List directory contents
  [green]tree [path][/green]            - Show directory tree structure
  [green]view [file][/green]            - View file content in preview panel
  [green]stat [file][/green]            - Show detailed file information
  [green]find [pattern] [path][/green]  - Search for files/directories

[b yellow]📄 FILE OPERATIONS[/b yellow]
  [green]open [file][/green]            - Open file with default application
  [green]edit [file][/green]            - Edit file with system editor
  [green]touch [file][/green]           - Create new empty file
  [green]mkdir [directory][/green]      - Create new directory

[b yellow]✂️ FILE MANAGEMENT[/b yellow]
  [green]copy / cp [src] [dest][/green] - Copy file or directory
  [green]move / mv [src] [dest][/green] - Move file or directory
  [green]rename / rn [old] [new][/green] - Rename file or directory
  [green]delete / rm [path][/green]     - Delete file or directory
  [green]chmod [mode] [file][/green]    - Change file permissions (octal)

[b yellow]🛠️ SYSTEM COMMANDS[/b yellow]
  [green]help[/green]                   - Show this help menu
  [green]clear[/green]                  - Clear the preview panel
  [green]quit / q / exit[/green]        - Quit the application

[b yellow]⌨️ KEYBOARD SHORTCUTS[/b yellow]
  [green]:[/green]                      - Enter command mode
  [green]Tab[/green]                    - Auto-complete commands & paths
  [green]Esc[/green]                    - Cancel command mode
  [green]q[/green]                      - Quit application
  [green]h[/green]                      - Toggle help panel
  [green]r[/green]                      - Refresh directory tree
  [green]Backspace[/green]              - Go to parent directory

[b yellow]🚀 TAB AUTO-COMPLETION[/b yellow]
  • Commands: Type partial command + Tab to complete
  • File paths: Type partial path + Tab to complete
  • Multiple matches: Shows list to choose from
  • Directories: Auto-adds trailing slash
  • Common prefix: Auto-completes to shared characters

[b yellow]📝 COMMAND EXAMPLES[/b yellow]
  [white]cd Documents/Projects[/white]     - Navigate to Projects directory
  [white]ls /home[/white]                  - List contents of /home
  [white]open report.pdf[/white]           - Open PDF with default app
  [white]edit script.py[/white]            - Edit Python script
  [white]touch newfile.txt[/white]         - Create new text file
  [white]mkdir my_project[/white]          - Create project directory
  [white]cp file1.txt file2.txt[/white]    - Copy file1 to file2
  [white]mv old.txt new.txt[/white]        - Rename/move file
  [white]rm temp_file[/white]              - Delete file
  [white]find "*.py"[/white]               - Find all Python files
  [white]chmod 755 script.sh[/white]       - Make script executable

[b yellow]🎨 FEATURES[/b yellow]
  • Full file preview with metadata
  • Directory tree visualization
  • File search functionality
  • Permission management
  • Cross-platform file opening
  • Smart tab completion
  • Visual file type indicators

[b cyan]💡 TIP: Use Tab completion to explore available commands and files quickly![/b cyan]
"""

class FileIcons:
    """Provides file type specific icons."""
    
    # Directory icons
    DIRECTORY = "📁"
    DIRECTORY_OPEN = "📂"
    HOME = "🏠"
    DESKTOP = "🖥️"
    DOCUMENTS = "📝"
    DOWNLOADS = "📥"
    PICTURES = "🖼️"
    MUSIC = "🎵"
    VIDEOS = "🎬"
    
    # File type categories
    TEXT = "📄"
    CODE = "📝"
    PYTHON = "🐍"
    JAVASCRIPT = "📜"
    HTML = "🌐"
    CSS = "🎨"
    JSON = "📋"
    MARKDOWN = "📖"
    
    # Documents
    PDF = "📕"
    WORD = "📘"
    EXCEL = "📗"
    POWERPOINT = "📙"
    
    # Media
    IMAGE = "🖼️"
    VIDEO = "🎬"
    AUDIO = "🎵"
    
    # Archives
    ARCHIVE = "🗜️"
    ZIP = "🗜️"
    TAR = "🗜️"
    RAR = "🗜️"
    
    # Executables
    EXECUTABLE = "⚡"
    APP = "📱"
    SCRIPT = "📜"
    
    # System
    CONFIG = "⚙️"
    DATABASE = "🗄️"
    LOG = "📊"
    LOCK = "🔒"
    SYMLINK = "🔗"
    
    # Special
    HIDDEN = "👁️"
    TRASH = "🗑️"
    FAVORITE = "⭐"
    
    @staticmethod
    def get_icon(path: str) -> str:
        """Get appropriate icon for file/directory."""
        if os.path.isdir(path):
            return FileIcons.get_directory_icon(path)
        else:
            return FileIcons.get_file_icon(path)
    
    @staticmethod
    def get_directory_icon(path: str) -> str:
        """Get icon for directory."""
        dir_name = os.path.basename(path).lower()
        
        # Special directories
        if path == os.path.expanduser("~"):
            return FileIcons.HOME
        elif "desktop" in dir_name:
            return FileIcons.DESKTOP
        elif "document" in dir_name:
            return FileIcons.DOCUMENTS
        elif "download" in dir_name:
            return FileIcons.DOWNLOADS
        elif "picture" in dir_name or "photo" in dir_name:
            return FileIcons.PICTURES
        elif "music" in dir_name or "audio" in dir_name:
            return FileIcons.MUSIC
        elif "video" in dir_name or "movie" in dir_name:
            return FileIcons.VIDEOS
        elif dir_name.startswith('.'):
            return FileIcons.HIDDEN
        else:
            return FileIcons.DIRECTORY
    
    @staticmethod
    def get_file_icon(path: str) -> str:
        """Get icon for file based on extension."""
        name = os.path.basename(path).lower()
        ext = os.path.splitext(path)[1].lower()
        
        # Hidden files
        if name.startswith('.'):
            return FileIcons.HIDDEN
        
        # Executable files
        if os.access(path, os.X_OK):
            return FileIcons.EXECUTABLE
        
        # Code files
        code_extensions = {
            '.py': FileIcons.PYTHON,
            '.js': FileIcons.JAVASCRIPT,
            '.ts': FileIcons.JAVASCRIPT,
            '.jsx': FileIcons.JAVASCRIPT,
            '.tsx': FileIcons.JAVASCRIPT,
            '.html': FileIcons.HTML,
            '.htm': FileIcons.HTML,
            '.css': FileIcons.CSS,
            '.scss': FileIcons.CSS,
            '.sass': FileIcons.CSS,
            '.json': FileIcons.JSON,
            '.xml': FileIcons.CONFIG,
            '.yaml': FileIcons.CONFIG,
            '.yml': FileIcons.CONFIG,
            '.md': FileIcons.MARKDOWN,
            '.markdown': FileIcons.MARKDOWN,
            '.txt': FileIcons.TEXT,
            '.rtf': FileIcons.TEXT,
        }
        
        if ext in code_extensions:
            return code_extensions[ext]
        
        # Document files
        document_extensions = {
            '.pdf': FileIcons.PDF,
            '.doc': FileIcons.WORD,
            '.docx': FileIcons.WORD,
            '.odt': FileIcons.WORD,
            '.xls': FileIcons.EXCEL,
            '.xlsx': FileIcons.EXCEL,
            '.ods': FileIcons.EXCEL,
            '.ppt': FileIcons.POWERPOINT,
            '.pptx': FileIcons.POWERPOINT,
            '.odp': FileIcons.POWERPOINT,
        }
        
        if ext in document_extensions:
            return document_extensions[ext]
        
        # Media files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff'}
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}
        audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma'}
        
        if ext in image_extensions:
            return FileIcons.IMAGE
        elif ext in video_extensions:
            return FileIcons.VIDEO
        elif ext in audio_extensions:
            return FileIcons.AUDIO
        
        # Archive files
        archive_extensions = {'.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.xz'}
        if ext in archive_extensions:
            return FileIcons.ARCHIVE
        
        # Config files
        config_extensions = {'.ini', '.cfg', '.conf', '.config'}
        if ext in config_extensions:
            return FileIcons.CONFIG
        
        # Database files
        db_extensions = {'.db', '.sqlite', '.sqlite3', '.mdb'}
        if ext in db_extensions:
            return FileIcons.DATABASE
        
        # Log files
        if ext == '.log':
            return FileIcons.LOG
        
        # Default
        return FileIcons.TEXT

class FilePreview(Static):
    """Displays file content or info."""

    def show_file(self, path: str):
        self.update("")
        icon = FileIcons.get_icon(path)
        
        if os.path.isdir(path):
            # Show directory info
            try:
                items = os.listdir(path)
                file_count = len([f for f in items if os.path.isfile(os.path.join(path, f))])
                dir_count = len([f for f in items if os.path.isdir(os.path.join(path, f))])
                stat_info = os.stat(path)
                mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                self.update(f"""{icon} [b cyan]{path}[/b cyan]

Files: {file_count}
Directories: {dir_count}
Total items: {len(items)}
Modified: {mod_time}
Size: {self.get_size(path)}""")
            except Exception as e:
                self.update(f"{icon} [b red]Error reading directory:[/b red] {e}")
            return
        
        # Show file info and content
        try:
            stat_info = os.stat(path)
            size = stat_info.st_size
            mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            file_info = f"""{icon} [b green]{path}[/b green]

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
            self.update(f"{icon} [b red]Error:[/b red] {e}")

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

class HelpPanel(ScrollableContainer):
    """Scrollable help panel."""
    
    def __init__(self):
        super().__init__()
        self.help_content = Static("", markup=True)
        
    def compose(self):
        yield self.help_content
        
    def show_help(self):
        """Update help content."""
        self.help_content.update(HELP_TEXT)

class FileExplorer(App):
    """TUI file explorer with comprehensive file operations and Tab completion."""
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
        ("tab", "auto_complete", "Auto-complete"),
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
        self.clipboard_buffer = None
        self.current_directory = os.getcwd()
        self.last_completion = None

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
            self.command_input = Input(
                placeholder="Type command and press Enter... Press 'h' for help", 
                id="cmdbar"
            )
            self.command_input.display = False
            yield self.command_input
            self.suggestions = CommandSuggestions(id="suggestions")
            self.suggestions.display = False
            yield self.suggestions
        yield Footer()

    async def on_mount(self):
        self.dir_tree.focus()
        self.status.update_status(f"Ready. Press ':' for command mode, 'h' for full help menu. Current dir: {self.current_directory}")

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
        self.status.update_status("Command mode: Type a command and press Enter. Press ESC to cancel. Use Tab for auto-completion.")

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
            self.status.update_status("Help closed. Press 'h' to show help again.")
        else:
            self.help_panel.display = True
            self.help_panel.show_help()
            self.status.update_status("Help menu opened. Press 'h' to close, or browse commands below.")

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

    async def action_auto_complete(self):
        """Handle Tab key for auto-completion."""
        if not self.command_input.display:
            return
        
        current_input = self.command_input.value
        if not current_input.strip():
            return

        parts = current_input.strip().split()
        
        if not parts:
            return
        
        if len(parts) == 1:
            await self.complete_command(parts[0])
        else:
            await self.complete_path(parts[-1], current_input)

    async def complete_command(self, partial_cmd: str):
        """Auto-complete command names."""
        matches = [cmd for cmd in self.MY_COMMANDS if cmd.startswith(partial_cmd)]
        
        if not matches:
            self.status.update_status(f"No commands match: {partial_cmd}")
            return
        
        if len(matches) == 1:
            self.command_input.value = matches[0] + " "
            self.command_input.cursor_position = len(matches[0]) + 1
            self.status.update_status(f"Completed command: {matches[0]}")
        else:
            common_prefix = self.find_common_prefix(matches)
            if common_prefix and common_prefix != partial_cmd:
                self.command_input.value = common_prefix
                self.command_input.cursor_position = len(common_prefix)
                self.status.update_status(f"Common prefix: {common_prefix}")
            else:
                self.suggestions.show_suggestions(matches)
                self.status.update_status(f"Multiple matches: {', '.join(matches)}")

    async def complete_path(self, partial_path: str, full_input: str):
        """Auto-complete file/directory paths."""
        if os.path.isabs(partial_path):
            base_dir = os.path.dirname(partial_path) or "/"
            search_pattern = os.path.basename(partial_path) or ""
        else:
            base_dir = self.current_directory
            search_pattern = partial_path

        if partial_path.startswith("~"):
            base_dir = os.path.expanduser("~")
            search_pattern = partial_path[2:] if len(partial_path) > 1 else ""

        try:
            if not os.path.exists(base_dir):
                self.status.update_status(f"Directory not found: {base_dir}")
                return

            items = []
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if not search_pattern.startswith('.') and item.startswith('.'):
                    continue
                if item.startswith(search_pattern):
                    items.append(item)
            
            if not items:
                self.status.update_status(f"No matches for: {partial_path}")
                return

            items.sort(key=lambda x: (not os.path.isdir(os.path.join(base_dir, x)), x.lower()))

            if len(items) == 1:
                completed_path = os.path.join(base_dir, items[0])
                if os.path.isdir(completed_path):
                    completed_path += "/"
                
                new_input = full_input.rsplit(partial_path, 1)[0] + completed_path
                self.command_input.value = new_input
                self.command_input.cursor_position = len(new_input)
                self.status.update_status(f"Completed: {items[0]}")
            else:
                common_prefix = self.find_common_prefix(items)
                if common_prefix and common_prefix != search_pattern:
                    completed_path = os.path.join(base_dir, common_prefix)
                    new_input = full_input.rsplit(partial_path, 1)[0] + completed_path
                    self.command_input.value = new_input
                    self.command_input.cursor_position = len(new_input)
                    self.status.update_status(f"Common prefix: {common_prefix}")
                else:
                    formatted_items = []
                    for item in items[:15]:
                        item_path = os.path.join(base_dir, item)
                        icon = FileIcons.get_icon(item_path)
                        formatted_items.append(f"{icon} {item}")
                    
                    self.suggestions.show_suggestions(formatted_items)
                    self.status.update_status(f"Multiple matches: {len(items)} items found")

        except Exception as e:
            self.status.update_status(f"Completion error: {e}")

    def find_common_prefix(self, items: list) -> str:
        """Find the common prefix among a list of strings."""
        if not items:
            return ""
        
        sorted_items = sorted(items)
        first = sorted_items[0]
        last = sorted_items[-1]
        
        min_length = min(len(first), len(last))
        common_prefix = []
        
        for i in range(min_length):
            if first[i] == last[i]:
                common_prefix.append(first[i])
            else:
                break
                
        return "".join(common_prefix)

    async def on_input_changed(self, event: Input.Changed):
        """Show command suggestions as user types."""
        if event.input.id != "cmdbar":
            return
            
        value = event.value.strip()
        if not value:
            self.suggestions.display = False
            return

        matches = [cmd for cmd in self.MY_COMMANDS if cmd.startswith(value)]
        self.suggestions.show_suggestions(matches[:8])

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
            elif main_cmd in ["stat", "info"] and args:
                await self.show_file_info(args[0])
            elif main_cmd in ["find"] and args:
                await self.find_files(args[0], args[1] if len(args) > 1 else ".")
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
        """List directory contents with icons."""
        if not os.path.isabs(path):
            path = os.path.join(self.current_directory, path)
        
        if os.path.exists(path):
            try:
                items = os.listdir(path)
                # Format items with icons
                formatted_items = []
                for item in sorted(items):
                    item_path = os.path.join(path, item)
                    icon = FileIcons.get_icon(item_path)
                    formatted_items.append(f"{icon} {item}")
                
                output = "\n".join(formatted_items)
                self.preview.update(f"{FileIcons.DIRECTORY_OPEN} [b cyan]Contents of {path}:[/b cyan]\n\n{output}")
            except Exception as e:
                self.status.update_status(f"Error listing directory: {e}")
        else:
            self.status.update_status(f"Path not found: {path}")

    async def show_tree(self, path: str):
        """Show directory tree with icons."""
        if not os.path.isabs(path):
            path = os.path.join(self.current_directory, path)
        
        try:
            tree_output = self.generate_tree(path, max_depth=3)
            self.preview.update(f"{FileIcons.DIRECTORY} [b cyan]Directory tree for {path}:[/b cyan]\n\n{tree_output}")
        except Exception as e:
            self.status.update_status(f"Error generating tree: {e}")

    def generate_tree(self, path: str, prefix: str = "", max_depth: int = 3, depth: int = 0) -> str:
        """Generate directory tree string with icons."""
        if depth > max_depth:
            return prefix + "└── ...\n"
        
        name = os.path.basename(path) or path
        icon = FileIcons.get_icon(path)
        result = prefix + "└── " + icon + " " + name + "\n"
        
        if os.path.isdir(path):
            try:
                items = sorted(os.listdir(path))
                for i, item in enumerate(items):
                    item_path = os.path.join(path, item)
                    is_last = i == len(items) - 1
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    result += self.generate_tree(item_path, new_prefix, max_depth, depth + 1)
            except PermissionError:
                result += prefix + "    └── 🔒 [Permission denied]\n"
        
        return result

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
            self.preview.show_file(path)
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
            octal_mode = int(mode, 8)
            os.chmod(path, octal_mode)
            self.status.update_status(f"Changed permissions of {path} to {mode}")
        except Exception as e:
            self.status.update_status(f"Error changing permissions: {e}")

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
                for dir in dirs:
                    if pattern.lower() in dir.lower():
                        matches.append(os.path.join(root, dir))
            
            if matches:
                # Format matches with icons
                formatted_matches = []
                for match in matches[:20]:
                    icon = FileIcons.get_icon(match)
                    formatted_matches.append(f"{icon} {match}")
                
                result = "\n".join(formatted_matches)
                if len(matches) > 20:
                    result += f"\n\n... and {len(matches) - 20} more matches"
                self.preview.update(f"🔍 [b cyan]Found {len(matches)} matches for '{pattern}':[/b cyan]\n\n{result}")
            else:
                self.preview.update(f"🔍 [b yellow]No matches found for '{pattern}' in {search_dir}[/b yellow]")
        except Exception as e:
            self.status.update_status(f"Error searching: {e}")

    async def refresh_tree(self):
        """Refresh directory tree."""
        self.dir_tree.path = self.current_directory
        self.status.update_status(f"Refreshed: {self.current_directory}")

if __name__ == "__main__":
    FileExplorer().run()
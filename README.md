# TUI File Explorer

A keyboard-driven file explorer for the terminal, written in Python with Textual. Browse a directory tree, preview files and manage local files through an integrated command bar.

## Features

- Directory tree with a file preview panel and status bar.
- Command and path autocomplete.
- Navigation, file search and file metadata commands.
- File creation, copying, moving, renaming and deletion.
- Built-in help and keyboard shortcuts.

## Run locally

You need Python 3, Git and a terminal. The repository does not yet pin a tested Python/Textual version combination.

```sh
git clone https://github.com/warriorsapt-dotcom/tuifileexplorer.git
cd tuifileexplorer
python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```sh
# macOS / Linux
source .venv/bin/activate
```

Then install Textual and start the app from the repository directory:

```sh
python -m pip install textual
python main.py
```

`main.py` loads `app.tcss` and starts in the current working directory.

## Keyboard controls

| Key | Action |
| --- | --- |
| `:` | Open command mode |
| `Tab` | Complete a command or path |
| `Esc` | Leave command mode |
| `h` | Toggle help |
| `r` | Refresh the directory tree |
| `Backspace` | Go to the parent directory |
| `q` | Quit |

## First commands

Press `:` before entering a command:

```text
pwd
ls
view main.py
stat main.py
find main .
help
```

File-management commands include `touch`, `mkdir`, `cp`, `mv`, `rename`, `rm` and `chmod`. These operate on real files; use a disposable directory when trying mutation commands. Opening files and launching an editor depend on your operating system and installed applications.

## Code map

- `main.py`: app layout, preview, command processing, completion and file operations.
- `app.tcss`: styling for the main application.
- Numbered `main*.py` and additional `app*.tcss` files: alternative development iterations; start with `main.py`.

## Development directions

- Pin and test supported Python and Textual versions.
- Add command-parser and file-operation tests using temporary directories.
- Consolidate development iterations and document platform-specific behavior.

# NetShow

A real-time network connection monitor with friendly service names built with Textual. Think of it like a much more useful and far less chaotic visually nettop combined with iotop and lsof. It will hold your place as data repaints, and you can click into an entry to view everything about the process - path, pid, friendly name, local and remote addresses, service status, working directory, cpu usage, threads, memory usage and active connections!

<img width="638" alt="image" src="https://github.com/user-attachments/assets/cdb035cb-415a-4e21-a6a7-181ffe709c1b" />

## Features

- Real-time monitoring of TCP network connections
- Friendly service names for common applications (Docker, Plex, VS Code, etc.)
- Detailed connection information with process details
- Modern terminal UI with intuitive navigation
- Support for both root (psutil) and non-root (lsof) operation

## Installation

Install using uv (recommended):

```bash
uv pip install -r pyproject.toml
```

Or install for development with extra dependencies:

```bash
uv pip install -r pyproject.toml --extra dev
```

## Usage

Run the application:

```bash
netshow
```

### Navigation

- **Arrow keys**: Navigate through connections
- **Enter**: View detailed connection information
- **Escape**: Return from detail view
- **q**: Quit the application

## Development

This project uses modern Python packaging standards with uv for fast dependency management.

### Setup

```bash
# Clone and install
git clone <repository-url>
cd netshow
uv pip install -r pyproject.toml --extra dev
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/
```

## Requirements

- Python 3.9+
- Unix-like system (macOS, Linux)
- `lsof` command (usually pre-installed)

## License

MIT

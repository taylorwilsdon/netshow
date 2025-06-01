# NetShow

A real-time network connection monitor with friendly service names built with Textual.

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
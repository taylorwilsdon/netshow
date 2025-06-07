<h1 align="center">🚦 NetShow</h1>
<p align="center"><em>Friendly, process-aware network monitoring for your terminal</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white" alt="Python versions">
  <img src="https://img.shields.io/github/license/taylorwilsdon/netshow?color=green" alt="License">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/code%20style-ruff-black?logo=ruff" alt="Code style: ruff">
  <img src="https://img.shields.io/badge/UI-Textual-purple" alt="Built with Textual">
  <img src="https://img.shields.io/badge/dependencies-uv-orange?logo=uv" alt="uv">
</p>

<div align="center">
  <video width="1012px" src="https://github.com/user-attachments/assets/97f5af92-ec0a-4243-9894-d0c9d9470e1a"></video>
</div>

---

<details>
<summary><strong>Table&nbsp;of&nbsp;Contents</strong></summary>

- [Features](#features)
- [Quickstart](#quickstart)
- [Usage](#usage)
- [Keybindings](#keybindings)
- [Development](#development)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)
</details>

---

## ✨ Features

| Capability | Details |
|------------|---------|
| **Live TCP monitor** | Refreshes every 3 s (configurable) while preserving scroll position |
| **Human-friendly service names** | Shows *Docker*, *Plex*, *VS Code*, etc. instead of cryptic binaries |
| **Deep process drill-down** | Path, PID, cmdline, cwd, threads, CPU %, memory %, open files, active connections |
| **Clickable / keyboard navigation** | Press `↵` or click a row for a dedicated detail screen; refresh pauses automatically |
| **Runs privileged <br>or unprivileged** | Uses `psutil` (root) for full fidelity, falls back to `lsof` if run as a regular user |
| **Modern Textual UI** | Smooth scrolling, dark theme, status bar with connection count & data source |
| **Zero-pain install** | Powered by [`uv`](https://github.com/astral-sh/uv) for lightning-fast dependency resolution |

---

## 🚀 Quickstart

```bash
# Install (recommended)
uv pip install netshow

# Run
netshow
````

> **Tip:** Without root/sudo, NetShow silently switches to `lsof` and still gives you most connections.

---

## 🛠️ Usage

```bash
netshow [--interval 1.0] [--no-colors]
```

| Option             | Description          | Default |
| ------------------ | -------------------- | ------- |
| `--interval <sec>` | Refresh rate (float) | `3.0`   |
| `--no-colors`      | Disable ANSI colors  | Off     |

### Keybindings

| Key / Mouse | Action           |
| ----------- | ---------------- |
| ↑ / ↓       | Move cursor      |
| ↵ / Click   | Open detail view |
| Esc / ←     | Back to list     |
| **q**       | Quit NetShow     |

---

## 👩‍💻 Development

```bash
git clone https://github.com/taylorwilsdon/netshow.git
cd netshow
uv sync --extra dev
```

### Quality Gates

```bash
pytest            # tests
ruff format .     # auto-format
ruff check .      # lint
mypy src/         # type check
```

---

## 📋 Requirements

* Python **≥ 3.9**
* macOS or Linux
* `lsof` (usually pre-installed)

---

## 🤝 Contributing

Pull requests and ⭐ stars are welcome! Found a bug or have a feature request? Please [open an issue](https://github.com/taylorwilsdon/netshow/issues).

---

## 📜 License

MIT – see [`LICENSE`](LICENSE) for full text.


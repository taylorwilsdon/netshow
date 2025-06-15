<div align="center">
<img align="center" width="50%" src="https://github.com/user-attachments/assets/51b8f028-2d25-4664-b4a1-44dcf9490140" />

### netshow · interactive, process-aware network monitoring for your terminal

<div style="margin: 20px 0;">

![Python versions](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white) ![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey) ![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-black?logo=ruff) ![Built with Textual](https://img.shields.io/badge/UI-Textual-purple) ![uv](https://img.shields.io/badge/dependencies-uv-orange?logo=uv)

</div>
</div>

---

<div align="center" width="600px">
  <video width="600px" src="https://github.com/user-attachments/assets/97f5af92-ec0a-4243-9894-d0c9d9470e1a"></video>
</div>

---

## ✨ **Features**

<table style="width: 100%; border-collapse: collapse;">
<tr>
<td width="35%" style="font-weight: bold;">🔍 Live TCP monitor</td>
<td>Refreshes every 3 s (configurable) while preserving scroll position</td>
</tr>
<tr>
<td style="font-weight: bold;">👤 Human-friendly service names</td>
<td>Shows <em>Docker</em>, <em>Plex</em>, <em>VS Code</em>, etc. instead of cryptic binaries</td>
</tr>
<tr>
<td style="font-weight: bold;">🔬 Deep process drill-down</td>
<td>Path, PID, cmdline, cwd, threads, CPU %, memory %, open files, active connections</td>
</tr>
<tr>
<td style="font-weight: bold;">🖱️ Clickable / keyboard navigation</td>
<td>Press <code>↵</code> or click a row for a dedicated detail screen; refresh pauses automatically</td>
</tr>
<tr>
<td style="font-weight: bold;">🔐 Runs privileged<br>or unprivileged</td>
<td>Uses <code>psutil</code> (root) for full fidelity, falls back to <code>lsof</code> if run as a regular user</td>
</tr>
<tr>
<td style="font-weight: bold;">🎨 Modern Textual UI</td>
<td>Smooth scrolling, dark theme, status bar with connection count & data source</td>
</tr>
<tr>
<td style="font-weight: bold;">⚡ Zero-pain install</td>
<td>Powered by <a href="https://github.com/astral-sh/uv"><code>uv</code></a> for lightning-fast dependency resolution</td>
</tr>
</table>

---

## 🚀 **Quickstart**

```bash
# uvx (easiest)
uvx netshow

# Local Builds
git clone git@github.com:taylorwilsdon/netshow.git
uv run netshow

```

> 💡 **Tip:** Without root/sudo, NetShow silently switches to `lsof` and still gives you most connections.

---

## 🛠️ **Usage**

```bash
netshow [--interval 1.0] [--no-colors]
```

### **Options**
| Option | Description | Default |
|--------|-------------|---------|
| `--interval <sec>` | Refresh rate (float) | `3.0` |
| `--no-colors` | Disable ANSI colors | Off |

### **Keybindings**
| Key / Mouse | Action |
|-------------|--------|
| **↑ / ↓** | Move cursor |
| **↵ / Click** | Open detail view |
| **Esc / ←** | Back to list |
| **q** | Quit NetShow |

---

## 👩‍💻 **Development**

```bash
git clone https://github.com/taylorwilsdon/netshow.git
cd netshow
uv sync --extra dev
```

### **Quality Gates**
```bash
pytest            # tests
ruff format .     # auto-format
ruff check .      # lint
mypy src/         # type check
```

---

## 📋 **Requirements**

• Python **≥ 3.9**  
• macOS or Linux  
• `lsof` (usually pre-installed)

---

## 🤝 **Contributing**

Pull requests and ⭐ stars are welcome! Found a bug or have a feature request? Please [open an issue](https://github.com/taylorwilsdon/netshow/issues).

---

## 📜 **License**

MIT – see [`LICENSE`](LICENSE) for full text.

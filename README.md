<div align="center">
<img align="center" width="50%" src="https://github.com/user-attachments/assets/51b8f028-2d25-4664-b4a1-44dcf9490140" />

### netshow · interactive, process-aware network monitoring for your terminal

<div style="margin: 20px 0;">

![Python versions](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white) ![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey) ![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-black?logo=ruff) ![Built with Textual](https://img.shields.io/badge/UI-Textual-purple) ![uv](https://img.shields.io/badge/dependencies-uv-orange?logo=uv)

</div>
</div>

---

<div align="center" width="600px">
  <video width="600px" src="https://github.com/user-attachments/assets/e110f7db-f803-4aad-bef8-c3e928eed6e5"></video>
</div>

---

### A quick plug for AI-Enhanced Docs
<details>
<summary>But why?</summary>

**This README was written with AI assistance, and here's why that matters**
>
> As a solo dev building open source tools that many never see outside use, comprehensive documentation often wouldn't happen without AI help. Using agentic dev tools like **Roo** & **Claude Code** that understand the entire codebase, AI doesn't just regurgitate generic content - it extracts real implementation details and creates accurate, specific documentation.
>
> In this case, Sonnet 4 took a pass & a human (me) verified them 7/10/25.
</details>

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
<td style="font-weight: bold;">📊 Real-time metrics</td>
<td>Live connection counts, bandwidth monitoring with per-interface selection</td>
</tr>
<tr>
<td style="font-weight: bold;">🔍 Advanced filtering</td>
<td>Regex-powered search with live filtering across all connection fields</td>
</tr>
<tr>
<td style="font-weight: bold;">🔄 Smart sorting</td>
<td>Sort by status or process name with optimized rendering for large datasets</td>
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
| **Ctrl+C** | Force quit (hard quit) |
| **Ctrl+R** | Force refresh |
| **e** | Toggle emoji display on/off |
| **f** | Toggle filter input |
| **/** | Quick search (focus filter) |
| **s** | Sort by connection status |
| **p** | Sort by process name |
| **i** | Cycle network interface for bandwidth monitoring |

### **Advanced Features**

**🔍 Filtering & Search**
- Press `f` or `/` to open the filter input
- Supports regex patterns for advanced matching
- Filters across process names, addresses, and connection status
- Live updates as you type (with debouncing)

**🎨 Emoji Toggle**
- Press `e` to toggle emoji display on/off for a cleaner interface
- When disabled, removes all emoji prefixes from UI elements
- Useful for terminals with limited emoji support or accessibility preferences
- Setting persists during the session

**📊 Bandwidth Monitoring**
- Real-time bandwidth display in the metrics bar
- Press `i` to cycle through network interfaces (`all`, `eth0`, `wlan0`, etc.)
- Accurate per-interface monitoring for multi-NIC hosts
- Automatic fallback to global stats if interface unavailable

**🔄 Smart Performance**
- Optimized table rendering for large connection sets (5k+ connections)
- In-place cell updates to prevent flicker during sorting
- Preserves scroll position and cursor during refreshes
- Debounced filter input to avoid excessive updates

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

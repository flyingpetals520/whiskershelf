<div align="center">
<img src="./static/cat_src_2.png" alt="WhiskerShelf — a cat stretching on the shelf" width="350" />

# 🐾 WhiskerShelf · 温馨文献书架

**A cozy local AI-powered paper library manager — with a cat on the shelf.**

Stack your research on a digital corkboard, and let a curious cat watch over the ones you read most recently.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Backend](https://img.shields.io/badge/Backend-Python%20stdlib%20%7C%200%20deps-success.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-Vanilla%20JS%20%7C%20No%20build-orange.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[English](#-features) · [中文说明](#-中文说明)



---

## ✨ Features

- 📚 **Local-first paper library** — drop PDFs into the folder, see them as beautiful cards instantly
- 🏷️ **Tag management** — preset taxonomy (24+ categories) + custom tags + AI-recommended tags
- 📝 **Per-paper notes & abstracts** — keep your reading notes and LLM-extracted abstracts alongside each paper
- ⭐ **Star & filter** — favorite the important ones, filter views by tag or starred status
- 👁️ **Reading stats** — auto-tracked read counts, last read time, and a "recently read" shelf
- 🐈 **A cat on your shelf** — four hand-drawn black cats, randomly picked each visit, lazy on top of your reading list
- 🤖 **AI reading habit analysis** — feed your reading history to an LLM, get personalized research direction suggestions
- 🔍 **AI semantic search** — search by intent, not just keywords
- 💡 **Idea Spark** — pick 2–4 papers, LLM collides them into novel research directions, with an exportable Markdown task brief ready for Claude Code
- 🧠 **Reasoning / Chain-of-Thought** — optional, lets you see the model's thinking process (DeepSeek-R1 / Qwen3-Thinking / GLM-4.5 / OpenAI o1)
- 📂 **Reveal in file manager** — one click to highlight the PDF in Windows Explorer / macOS Finder
- ⌨️ **Keyboard shortcut** — `Ctrl+S` saves tag edits without leaving the keyboard
- 🌗 **Light / dark theme** — paper-warm by day, ink-blue by night
- 🔌 **Zero third-party dependencies** — only the Python standard library (and optional `PyPDF2` for PDF abstract extraction)

---

## 🖼️ Preview

> Coming soon: animated GIF / screenshot gallery

| View | Description |
|---|---|
| 🏠 **Main board** | Paper cards with tag stickers, abstracts, notes, stats |
| 🧠 **AI 分析** | LLM-analyzed reading habits with persistent history |
| 💡 **Idea Spark** | Cross-paper brainstorming with downloadable Markdown brief |
| ⚙️ **Settings** | API key, base URL, model, thinking mode toggle |

---

## 🚀 Quick Start

### 1. Requirements

- Python 3.8 or newer
- (Optional) `PyPDF2` for automatic abstract extraction from PDFs:
  ```bash
  pip install PyPDF2
  ```

### 2. Get the code

```bash
git clone https://github.com/<your-username>/whiskershelf.git
cd whiskershelf
```

Or just download / unzip the release into any folder.

### 3. Run

**Windows** — double-click `start.bat`, or:

```bat
python app.py
```

**macOS / Linux**:

```bash
python3 app.py
```

Then open your browser at **<http://127.0.0.1:8080>**

That's it. The first time you start, the app will:
- Scan the current folder for PDF files
- Initialize empty `paper_tags.json`, `paper_reading.json`, etc.
- Show the cat on the empty shelf, waiting for you to read

### 4. Drop your PDFs in

Just copy any `.pdf` files into the same folder as `app.py`. Click 🔄 **刷新** in the toolbar to re-scan. The cat will re-roll, papers will appear as cards.

---

## 🤖 AI Setup (Optional)

AI features are off by default. To enable them:

1. Click **⚙️ 设置** in the top-right
2. Toggle **启用 AI 功能**
3. Fill in:
   - **API Key** — your OpenAI-compatible API key (e.g. DeepSeek, GLM, Kimi, Qwen, OpenAI)
   - **Base URL** — default `https://api.deepseek.com/v1`
   - **模型** — e.g. `deepseek-chat`, `deepseek-reasoner`, `gpt-4o`, `qwen3-...`
4. (Optional) Enable **启用思考模式** for reasoning models to expose their chain-of-thought
5. (Optional) Adjust **思考 token 预算** (default 2048)
6. Click **🧪 测试连接**

> 💡 Your API key is stored in `ai_config.json` (gitignored by default). See `ai_config.example.json` for the template.

Any OpenAI-compatible endpoint works. Verified providers include:
- **DeepSeek** (deepseek-chat, deepseek-reasoner)
- **智谱 GLM** (glm-4.5, glm-4.5v, ...)
- **Kimi / Moonshot** (kimi-k2-..., moonshot-v1-...)
- **Qwen / 阿里通义** (qwen3-..., qwen-vl-...)
- **OpenAI** (gpt-4o, o1-mini, o3-mini)
- **Local** (Ollama, vLLM, LM Studio, etc.)

---

## 📁 Project Structure

```
whiskershelf/
├── app.py                        # Main server (Python stdlib only)
├── start.bat                     # Windows launcher with friendly banner
├── tag_presets.json              # Default tag taxonomy (shipped)
├── ai_config.example.json        # Template for AI configuration
├── LICENSE                       # MIT
├── README.md                     # You are here
├── .gitignore                    # Excludes user data & secrets
│
├── static/                       # Frontend assets
│   ├── index.html                # Single-page app
│   ├── style.css                 # Cozy paper / cat theme
│   ├── app.js                    # Vanilla JS client
│   └── cat_src*.png              # Four black cat illustrations
│
└── (auto-created on first run)
    ├── paper_tags.json           # Per-paper tags
    ├── paper_reading.json        # Read counts, star status
    ├── paper_abstracts.json      # LLM-extracted abstracts
    ├── paper_notes.json          # Per-paper reading notes
    ├── analysis_history.json     # AI analysis session history
    ├── idea_spark_history.json   # Idea Spark session history
    └── ai_config.json            # Your API key & settings
```

---

## 🧰 Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python `http.server` (stdlib) | Zero install, zero deps, fast enough for personal use |
| PDF parsing | `PyPDF2` (optional) | Best-in-class pure-Python PDF text extraction |
| LLM API | OpenAI-compatible chat completions | Works with 20+ providers out of the box |
| Frontend | Vanilla HTML / CSS / JS | No build step, no framework lock-in, instant edit-and-reload |
| Storage | Local JSON files | Human-readable, easy to back up, easy to migrate |

**No npm, no virtualenv, no bundler, no transpiler.** Clone, run, done.

---

## 🤖 AI Features in Detail

### 🔍 AI Semantic Search

Type something like *"spiking neural networks for time series"* and get a ranked list of relevant papers — even if the words don't match any title. The LLM sees the candidate set and judges relevance semantically.

### 🏷️ AI Tag Recommendation

Open any paper's edit modal → click **🤖 AI推荐**. The LLM reads the abstract and the tag taxonomy, suggests 1–3 most-fitting tags. One click to apply.

### 🧠 AI Reading Habit Analysis

Click **🧠 AI分析** in the toolbar. The LLM receives:
- Your top 5 recently read papers
- All papers you've read more than once
…and returns a structured analysis of:
- Your research focus areas
- Coverage gaps you might want to fill
- Concrete reading recommendations

History is saved server-side and survives browser restarts, device switches, and clear-cache operations.

### 💡 Idea Spark

This is the headline feature. Click **💡 Idea spark**:

1. Search your library, pick 2–4 papers
2. Optionally add research context / constraints
3. Click **✨ 火花碰撞!**

The LLM acts as a "research innovation catalyst", producing a structured Markdown brief with:
- Common themes and methodological tensions across the papers
- 3–5 actionable research directions, each with: core idea / method transfer path / expected challenges / minimal experiment
- Cross-domain leap suggestions (e.g., "can we apply SNN to financial time series?")
- Risk and blind-spot analysis
- **A ready-to-paste Claude Code task block** — a `.md` you can drop into Claude Code and say "go"

Click **💾 下载为 .md** to get the full session — including the model's chain-of-thought when thinking mode is on.

### 🧠 Reasoning / CoT (Optional)

For models that support chain-of-thought (DeepSeek-R1, Qwen3-Thinking, GLM-4.5, OpenAI o1/o3):
1. Enable **启用思考模式** in settings
2. The model's reasoning appears in a collapsible **💭 思考过程** panel above the result
3. Also exported into the downloaded `.md`

---

## 💡 Innovations

What makes WhiskerShelf different from the dozens of existing paper managers?

1. **No-cloud-by-default** — your PDFs never leave your disk. AI features are opt-in and the data sent is just titles, abstracts, and notes.
2. **Truly zero-dependency backend** — you can audit every line. No `pip install` of mysterious packages. Runs on a Raspberry Pi.
3. **LLM-collaborative research assistant**, not just a search box — Idea Spark turns paper reading into research planning.
4. **Exportable AI output** — Idea Spark results are first-class Markdown, designed to be handed to Claude Code as a task spec.
5. **Reasoning visibility** — when the model thinks, you see it. No black-box.
6. **Server-side history persistence** — Idea Spark and analysis sessions live in JSON files, so they survive browser changes, follow you between machines, and are easy to back up.
7. **Localstorage migration** — older versions used browser localStorage; on first visit, the app automatically migrates your data to server JSON.
8. **A cat on the shelf** — because reading papers shouldn't feel like filling out a database.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action | Context |
|---|---|---|
| `Ctrl + S` / `Cmd + S` | Save tag & notes edits | When the edit-tag modal is open |
| `Esc` | Close any open modal | Global (via overlay click, ESC planned) |

---

## 🛠️ Configuration

### Tag Presets

Edit `tag_presets.json` to add/remove default tags. Or use **🏷️ 管理标签** in the UI.

### Cat Preferences

Edit `static/app.js` near `CAT_TOP_OFFSETS` (around line 69) to adjust each cat's vertical position:

```js
const CAT_TOP_OFFSETS = {
    'cat_src.png':   -52,   // smaller absolute value = cat sits lower
    'cat_src_1.png': -88,
    'cat_src_2.png': -82,
    'cat_src_3.png': -82,
};
```

To pin a specific cat (instead of random), temporarily edit the `catImages` array in the same file.

### Theming

Edit CSS variables in `static/style.css` (`:root` block) for paper color, accent, font, etc.

---

## 🐛 Troubleshooting

| Symptom | Fix |
|---|---|
| Port 8080 in use | Edit `PORT = 8080` in `app.py` |
| AI features greyed out | Fill in API key, enable in 设置 |
| "AI未配置或已禁用" | Same as above |
| "请选择 2-4 篇论文" | Idea Spark needs at least 2 papers selected |
| Cat not visible | Make sure the "最近阅读" shelf has at least one paper (open any PDF first) |
| PDFs not appearing | Click 🔄 刷新; check file extension is `.pdf` (case-insensitive) |
| Encoding garbled in terminal (Windows) | The app already sets `PYTHONIOENCODING=utf-8` in `start.bat`; for `python app.py` direct, run `chcp 65001` first |

---

## 🤝 Contributing

PRs welcome! Some ideas:

- [ ] More cat poses (open a PR with your favorite black-cat SVG/PNG!)
- [ ] PDF full-text indexing for offline semantic search
- [ ] BibTeX export
- [ ] Multi-library support (currently single-folder)
- [ ] WebSocket for live re-scan
- [ ] Mobile-friendly layout polish

Please keep dependencies minimal — the spirit of the project is "stdlib + a sprinkle of LLM".

---

## 📜 License

[MIT](./LICENSE) — do anything you want, just keep the copyright notice.

---

## 🙏 Acknowledgements

- The black cat illustrations are hand-drawn and shipped with the project; feel free to replace them with your own favorites.
- Inspired by countless hours of paper-reading, the cozy-app aesthetic of Things / Bear, and the dream of a research assistant that doesn't phone home.
- Built with the help of [DeepSeek](https://deepseek.com), [GLM](https://www.zhipuai.cn), [Kimi](https://kimi.moonshot.cn), and the open-source LLM community.

---

## 🐾 中文说明

**WhiskerShelf（温馨文献库）** 是一个本地优先的 AI 增强论文管理工具。零后端依赖（只用 Python 标准库），前端原生 JS / CSS / HTML 不需要打包。

把 PDF 放进文件夹，它们就会变成一张张带便签的论文卡片；编辑模态框里能打标签、贴摘要、写笔记；每张论文卡片的右上角有 4 个按钮——⭐ 收藏、📂 打开文件位置、🏷️ 编辑标签、📖 打开 PDF。还有一只黑色小猫趴在"最近阅读"框上看你读书。

**AI 能力**（全部可选，需要在设置里填入 OpenAI 兼容 API Key）：

- 🤖 **AI 语义搜索** — 用自然语言找论文，不依赖关键词匹配
- 🏷️ **AI 推荐标签** — 给论文摘要，AI 自动从标签库选最匹配的 1-3 个
- 🧠 **AI 阅读习惯分析** — 把你的阅读记录交给 LLM，输出研究方向、知识盲点、推荐论文
- 💡 **Idea Spark（核心）** — 选 2-4 篇论文，AI 跨论文碰撞，输出**结构化 Markdown 研究方向**，可直接喂给 Claude Code 当任务说明执行。开启思考模式还能看到模型的思维链。

**键盘快捷键**：编辑标签时按 `Ctrl+S`（Mac: `Cmd+S`）保存。

**历史持久化**：所有 AI 会话都存在服务端的 JSON 文件中，换浏览器、换电脑都不会丢，老版本 localStorage 的数据首次访问时会自动迁移。

**完全离线可用**：AI 功能关掉就是一个纯本地文献管理工具。

<div align="center">

Made with 🐾 for paper lovers who also love cats.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper Library Manager - 本地论文标签管理系统
基于 Python 标准库，零第三方依赖
"""

import json
import os
import sys
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# 配置
# ROOT 决定哪里是"用户数据目录"（PDFs + JSON 数据文件）
# 默认是当前工作目录；可用 --root <path> 覆盖：
#   python app.py --root "E:/my-papers"
import sys
_arg_root = None
if "--root" in sys.argv:
    _i = sys.argv.index("--root")
    if _i + 1 < len(sys.argv):
        _arg_root = sys.argv[_i + 1]
if _arg_root:
    ROOT = Path(_arg_root).expanduser().resolve()
else:
    ROOT = Path(".").resolve()
STATIC_DIR = Path(__file__).resolve().parent / "static"  # static 永远在 app.py 同目录
SKILLS_DIR = Path(__file__).resolve().parent / "whiskershelf-skills"  # 顶层 skills 模板目录
TAGS_FILE = ROOT / "paper_tags.json"
PRESETS_FILE = ROOT / "tag_presets.json"
READING_FILE = ROOT / "paper_reading.json"
NOTES_FILE = ROOT / "paper_notes.json"
PORT = 8080

# 确保 static 目录存在
STATIC_DIR.mkdir(exist_ok=True)


def load_tags():
    """加载标签数据，如果不存在则扫描PDF初始化"""
    if TAGS_FILE.exists():
        try:
            with open(TAGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # 初始化：扫描所有PDF
    tags = {}
    for f in sorted(ROOT.iterdir()):
        if f.is_file() and f.suffix.lower() == ".pdf":
            tags[f.name] = []
    save_tags(tags)
    return tags


def save_tags(tags):
    """保存标签数据"""
    with open(TAGS_FILE, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)


def load_abstracts():
    """加载论文摘要数据"""
    if ABSTRACTS_FILE.exists():
        try:
            with open(ABSTRACTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_abstracts(abstracts):
    """保存论文摘要数据"""
    with open(ABSTRACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(abstracts, f, ensure_ascii=False, indent=2)


def load_idea_spark_history():
    """加载 Idea Spark 历史会话"""
    if IDEA_SPARK_HISTORY_FILE.exists():
        try:
            with open(IDEA_SPARK_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sessions": []}


def save_idea_spark_history(data):
    """保存 Idea Spark 历史会话"""
    with open(IDEA_SPARK_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_analysis_history():
    """加载 AI 分析历史会话"""
    if ANALYSIS_HISTORY_FILE.exists():
        try:
            with open(ANALYSIS_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sessions": []}


def save_analysis_history(data):
    """保存 AI 分析历史会话"""
    with open(ANALYSIS_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_analysis_session(analysis_content):
    """保存一次 AI 分析结果到历史"""
    data = load_analysis_history()
    session = {
        "id": str(int(time.time() * 1000)),
        "time": int(time.time()),
        "analysis": analysis_content
    }
    data["sessions"].insert(0, session)
    # 最多保留 50 条
    if len(data["sessions"]) > 50:
        data["sessions"] = data["sessions"][:50]
    save_analysis_history(data)
    return session


def get_analysis_session(session_id):
    """根据 id 获取单条 AI 分析会话"""
    data = load_analysis_history()
    for s in data.get("sessions", []):
        if s.get("id") == session_id:
            return s
    return None


def load_reading():
    """加载论文阅读记录"""
    if READING_FILE.exists():
        try:
            with open(READING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_reading(data):
    """保存论文阅读记录"""
    with open(READING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_notes():
    """加载论文阅读笔记"""
    if NOTES_FILE.exists():
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_notes(data):
    """保存论文阅读笔记"""
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_abstract_from_pdf(file_path):
    """从PDF中提取Abstract/摘要文本"""
    try:
        import re
        from PyPDF2 import PdfReader
        reader = PdfReader(str(file_path))
        text = ""
        # 只读前3页（摘要通常在前面）
        for i, page in enumerate(reader.pages[:3]):
            try:
                text += page.extract_text() + "\n"
            except Exception:
                continue
        if not text.strip():
            return ""
        
        # 清理文本：把连字符断词恢复
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # 尝试多种Abstract格式
        patterns = [
            # 英文 Abstract ... Introduction/Keywords/1.
            r'Abstract\s*[\:：]?\s*(.+?)(?=\s+(?:Introduction|Keywords|Key words|1\s+Introduction|I\s+INTRODUCTION|Background|Related Work|Motivation|\Z))',
            # 全大写 ABSTRACT
            r'ABSTRACT\s*[\:：]?\s*(.+?)(?=\s+(?:INTRODUCTION|KEYWORDS|BACKGROUND|RELATED WORK|MOTIVATION|\Z))',
            # 中文 摘要 ... 关键词/引言/1.
            r'摘\s*要\s*[\:：]?\s*(.+?)(?=\s+(?:关键词|关\s*键\s*词|引言|1\s|一\s|绪论|背景|相关研究|\Z))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # 清理一些常见噪音
                abstract = re.sub(r'^\d+\s*', '', abstract)  # 去掉开头的数字编号
                abstract = abstract.strip()
                if len(abstract) > 30:  # 至少30个字符才算有效摘要
                    return abstract[:2000]  # 限制长度
        return ""
    except Exception as e:
        print(f"[Extract Abstract Error] {e}")
        return ""


def get_papers():
    """获取所有论文及标签"""
    tags = load_tags()
    abstracts = load_abstracts()
    reading = load_reading()
    notes = load_notes()
    papers = []
    for f in sorted(ROOT.iterdir()):
        if f.is_file() and f.suffix.lower() == ".pdf":
            name = f.name
            # 友好显示名称：去掉.pdf，截断过长
            display = name
            if display.lower().endswith(".pdf"):
                display = display[:-4]
            stat = f.stat()
            papers.append({
                "name": name,
                "display": display,
                "tags": tags.get(name, []),
                "mtime": stat.st_mtime,
                "abstract": abstracts.get(name, ""),
                "read_count": reading.get(name, {}).get("read_count", 0),
                "last_read": reading.get(name, {}).get("last_read", 0),
                "starred": reading.get(name, {}).get("starred", False),
                "notes": notes.get(name, ""),
            })
    # 将标签数据中没有的PDF也补进去（新文件）
    updated = False
    for p in papers:
        if p["name"] not in tags:
            tags[p["name"]] = []
            updated = True
    if updated:
        save_tags(tags)
    return papers


def load_presets():
    """加载预设标签库"""
    if PRESETS_FILE.exists():
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    defaults = [
        "强化学习 RL",
        "线性注意力",
        "Transformer",
        "大语言模型 LLM",
        "多模态",
        "计算机视觉 CV",
        "图像生成",
        "视频生成",
        "脉冲神经网络 SNN",
        "神经形态计算",
        "脑科学",
        "优化器",
        "扩散模型",
        "世界模型",
        "Agent",
        "记忆网络",
        "语音音频",
        "机器人",
        "高效推理",
        "训练方法",
        "架构创新",
        "开源模型",
        "理论分析"
    ]
    save_presets(defaults)
    return defaults


def save_presets(presets):
    """保存预设标签库"""
    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, ensure_ascii=False, indent=2)


def get_all_tags():
    """获取所有不重复标签（包含预设和已使用的）"""
    tags = load_tags()
    all_tags = set(load_presets())
    for tlist in tags.values():
        for t in tlist:
            if t.strip():
                all_tags.add(t.strip())
    return sorted(all_tags, key=lambda x: x.lower())


# ==================== AI 功能 ====================
AI_CONFIG_FILE = ROOT / "ai_config.json"
ABSTRACTS_FILE = ROOT / "paper_abstracts.json"
IDEA_SPARK_HISTORY_FILE = ROOT / "idea_spark_history.json"
ANALYSIS_HISTORY_FILE = ROOT / "analysis_history.json"

IDEA_SPARK_SYSTEM_PROMPT = """你是一位科研创新催化剂，擅长从多篇论文中"碰撞"出可执行的研究方向。用户会给你 2-4 篇不同/相关领域的论文信息（每篇包含：标题、标签、摘要、用户笔记），你的任务是跨越这些论文的边界，发现隐藏的研究机会。

**注意**：每篇论文除了标题和摘要外，还会附带：
- **标签**：用户给论文打的领域/方法标签（如"线性注意力"、"脉冲神经网络"），可用于快速识别论文所属领域
- **用户笔记**：用户自己记录的阅读心得/关键结论，可能包含摘要没有的洞察

请充分利用所有这些信息来产出更精准的碰撞。

**输出要求：纯 Markdown 格式**，按以下结构组织（必须包含全部小节）：

## 1. 共同主题与张力
- 这些论文在主题、方法、假设上的共同点
- 内在的方法论张力或矛盾点（这是创新的种子）

## 2. 跨论文灵感方向（3-5 个）
每条必须包含：
- **核心 Idea**：一句话概括
- **方法迁移路径**：从哪篇借鉴什么、改造什么
- **预期难点**：可能遇到的挑战
- **验证方案**：最小可行实验

鼓励把 A 领域的方法迁移到 B 领域，把 B 的视角重新审视 A。

## 3. 跨领域联想
- 把上述方法迁移到一个完全不相关领域（如把 SNN 用到金融时序、把扩散模型用到分子设计）
- 至少 1 条，列举 1-3 个具体领域 + 切入点

## 4. 风险与盲区
- 一句话指出这些 idea 可能的失败原因或被忽略的反例

## 5. Claude Code 任务指令
最后给出一个 ```markdown 代码块，里面是**可以直接粘贴到 Claude Code** 的任务指令，格式如下：
```
# 任务：[简洁任务名]

## 背景
[基于上述 idea 的上下文]

## 目标
[具体要达成的目标]

## 步骤
1. [步骤一]
2. [步骤二]
...

## 验收标准
- [ ] [标准一]
- [ ] [标准二]
```

**风格要求**：
- 中文回答
- 技术具体，避免"提高性能"等空话，要说"在 CIFAR-10 上把 top-1 提到 X%"
- 编号、列表、加粗合理使用
- 不要寒暄、不要总结、直接进入分析
"""


def load_ai_config():
    """加载AI配置"""
    if AI_CONFIG_FILE.exists():
        try:
            with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "enabled": False,
        "thinking_enabled": False,
        "thinking_budget": 2048,
        "cc_project_dir": ""  # 用户配置：CC 项目默认输出目录（空=用内置默认）
    }


def save_ai_config(cfg):
    """保存AI配置"""
    with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_default_cc_project_base():
    """解析用户配置的 CC 项目输出基础目录。空值/无效值 → 内置默认。"""
    cfg = load_ai_config()
    raw = (cfg.get("cc_project_dir") or "").strip()
    if raw:
        # 展开 ~ 和环境变量
        candidate = Path(raw).expanduser()
        try:
            candidate = candidate.resolve()
        except Exception:
            return None
        return candidate
    # 内置默认：<user-home>/Documents/whiskershelf-briefs/
    return Path.home() / "Documents" / "whiskershelf-briefs"


def call_llm(messages, config, max_tokens=2048):
    """调用LLM API（兼容OpenAI格式）

    返回: (content, reasoning_content)
        - content: 模型最终回答
        - reasoning_content: 思维链内容（仅推理模型支持时存在；否则为 None）
    """
    import urllib.request
    api_key = config.get("api_key", "").strip()
    base_url = config.get("base_url", "https://api.deepseek.com/v1").strip().rstrip("/")
    model = config.get("model", "deepseek-chat").strip()
    if not api_key:
        raise ValueError("API Key 未配置")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tokens
    }
    # 思考模式：同时发送多种 provider 风格的参数（兼容 DeepSeek-R1、Qwen3-Thinking、GLM-4.5、OpenAI o1 等）
    if config.get("thinking_enabled"):
        budget = int(config.get("thinking_budget") or 2048)
        # Qwen3 / GLM-4.5 风格
        payload["enable_thinking"] = True
        payload["thinking_budget"] = budget
        # OpenAI o1/o3 风格
        payload["reasoning_effort"] = "medium"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read().decode("utf-8"))
        msg = result["choices"][0]["message"]
        content = (msg.get("content") or "").strip()
        # DeepSeek-R1 等推理模型会在 message 中返回 reasoning_content 字段
        reasoning_content = msg.get("reasoning_content")
        if reasoning_content:
            reasoning_content = reasoning_content.strip()
        return content, reasoning_content
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"API错误 {e.code}: {body}")
    except Exception as e:
        raise RuntimeError(f"请求失败: {e}")


def ai_semantic_search(query, papers, presets, config):
    """AI语义搜索"""
    # 为标签附上定义，帮助AI理解查询意图
    tag_desc_lines = []
    for t in presets:
        desc = _TAG_DEFINITIONS.get(t, "")
        if desc:
            tag_desc_lines.append(f"- {t}：{desc}")
    tag_desc_str = "\n".join(tag_desc_lines)

    # 只取前100篇避免超出token限制
    display_papers = papers[:100]
    paper_list = []
    for i, p in enumerate(display_papers):
        entry = f"{i+1}. 标题：{p['name']}"
        if p.get("abstract"):
            # 截断摘要避免过长
            ab = p["abstract"][:300]
            entry += f"\n   摘要：{ab}"
        paper_list.append(entry)
    paper_list_str = "\n".join(paper_list)

    messages = [
        {"role": "system", "content": "你是一位学术文献检索专家。用户会用自然语言描述他想找的论文方向。请从给定的论文列表中，选出最相关的论文（最多10篇）。\n\n判断标准：\n1. 综合标题和摘要判断相关性\n2. 匹配用户查询的核心主题、方法、任务\n3. 不仅看关键词，更要理解语义\n4. 优先选择方法/模型/任务最契合的论文\n\n只返回论文的完整文件名（精确匹配），每行一个。不要输出任何解释。如果没有相关的，只返回'无'。"},
        {"role": "user", "content": f"标签定义参考：\n{tag_desc_str}\n\n论文列表（共{len(display_papers)}篇）：\n{paper_list_str}\n\n用户查询：{query}\n\n请返回最相关的论文文件名（最多10篇）："}
    ]
    content, _ = call_llm(messages, config)
    if content == "无" or not content:
        return []
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    # 清理可能的序号前缀
    cleaned = []
    for line in lines:
        if ". " in line[:4]:
            line = line.split(". ", 1)[1]
        elif line.startswith("-"):
            line = line[1:].strip()
        cleaned.append(line)
    return cleaned


# 标签定义说明，帮助AI更准确理解每个标签
_TAG_DEFINITIONS = {
    "强化学习 RL": "策略优化、奖励模型、PPO/GRPO/DPO、Q-learning、 actor-critic",
    "线性注意力": "线性复杂度注意力、RWKV、Mamba、State Space Models、长序列建模",
    "Transformer": "标准Transformer、BERT、GPT、注意力机制改进、位置编码",
    "大语言模型 LLM": "LLM预训练、微调、对齐、推理、长上下文、Scaling Law",
    "多模态": "图文联合建模、VLM、跨模态学习、视觉语言模型",
    "计算机视觉 CV": "图像分类、检测、分割、视觉表征、自监督视觉",
    "图像生成": "扩散模型、GAN、VAE、文生图、图像编辑",
    "视频生成": "视频合成、时序建模、文生视频、视频预测",
    "脉冲神经网络 SNN": "Spiking Neural Network、事件驱动、时序编码、 surrogate gradient",
    "神经形态计算": "类脑芯片、神经形态硬件、忆阻器、脑启发计算",
    "脑科学": "神经回路、脑区功能、认知神经科学、皮层结构、海马体",
    "优化器": "训练优化算法、学习率调度、Adam/SGD变种、二阶优化",
    "扩散模型": "Diffusion Models、Score-based、流匹配Flow Matching、DDPM",
    "世界模型": "环境模拟、JEPA、预测架构、下一状态预测、具身智能",
    "Agent": "智能体、工具使用、自主决策、ReAct、规划、多智能体",
    "记忆网络": "外置记忆、检索增强RAG、长时记忆、Memory Augmented",
    "语音音频": "ASR、TTS、语音合成、音频分离、声纹识别",
    "机器人": "机械臂控制、运动规划、机器人学习、VLA、操作技能",
    "高效推理": "模型量化、剪枝、蒸馏、投机解码、边缘部署",
    "训练方法": "数据增强、课程学习、自监督、对比学习、元学习",
    "架构创新": "MoE、新型网络结构、模块设计、NAS、动态网络",
    "开源模型": "模型开源发布、技术报告、社区模型、模型权重",
    "理论分析": "可解释性、表达能力、收敛性、复杂度分析、下界证明"
}


def ai_recommend_tags(title, abstract, presets, config):
    """AI自动推荐标签"""
    # 为每个标签附上定义
    preset_lines = []
    for t in presets:
        desc = _TAG_DEFINITIONS.get(t, "")
        if desc:
            preset_lines.append(f"- {t}：{desc}")
        else:
            preset_lines.append(f"- {t}")
    preset_str = "\n".join(preset_lines)

    content_parts = [f"论文标题：{title}"]
    if abstract and abstract.strip():
        content_parts.append(f"论文摘要：{abstract.strip()[:800]}")
    content_parts.append("请推荐最匹配的1-3个标签（只写标签名）：")
    user_content = "\n\n".join(content_parts)

    messages = [
        {"role": "system", "content": "你是一位顶级AI学术分类专家。请根据论文的标题和摘要，从给定的预设标签中选择最合适的1-3个标签。每个标签都有详细定义说明。只返回标签名称本身，每行一个。不要返回定义说明。不要输出任何解释。不要编造不在列表中的标签。"},
        {"role": "user", "content": f"预设标签列表（含定义）：\n{preset_str}\n\n{user_content}"}
    ]
    content, _ = call_llm(messages, config)
    if not content or content == "无":
        return []
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    cleaned = []
    for line in lines:
        # 去掉可能的序号或破折号前缀
        if ". " in line[:4]:
            line = line.split(". ", 1)[1]
        elif line.startswith("-"):
            line = line[1:].strip()
        # 去掉可能的定义部分（AI有时会返回"标签：定义"）
        if "：" in line or ":" in line:
            line = line.split("：")[0].split(":")[0].strip()
        # 精确匹配预设标签
        if line in presets and line not in cleaned:
            cleaned.append(line)
    return cleaned


def ai_idea_spark(papers_info, user_context, config):
    """Idea Spark 跨论文灵感碰撞

    papers_info: [{"name": str, "title": str, "abstract": str, "tags": [...], "notes": str}, ...]
    user_context: 用户补充的研究背景/约束（可空）
    返回: {"success": True, "content": "...", "papers": [...], "user_context": "..."}
    """
    # 拼接论文信息：标题 + 标签 + 摘要（更长） + 笔记
    paper_blocks = []
    for i, p in enumerate(papers_info, 1):
        block = f"【论文 {i}】\n标题：{p.get('title', p.get('name', ''))}"
        tags = p.get("tags") or []
        if tags:
            block += f"\n标签：{', '.join(tags)}"
        ab = (p.get("abstract") or "").strip()
        if ab:
            block += f"\n摘要：{ab[:2000]}"
        notes = (p.get("notes") or "").strip()
        if notes:
            block += f"\n用户笔记：{notes[:500]}"
        paper_blocks.append(block)
    papers_str = "\n\n".join(paper_blocks)

    user_parts = [f"以下是用户选中的 {len(papers_info)} 篇论文：\n\n{papers_str}"]
    if user_context and user_context.strip():
        user_parts.append(f"\n\n【用户补充的研究背景/约束】\n{user_context.strip()}")
    user_parts.append("\n\n请按 system prompt 要求的结构输出 Markdown 形式的灵感火花。")
    user_content = "".join(user_parts)

    messages = [
        {"role": "system", "content": IDEA_SPARK_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    content, reasoning_content = call_llm(messages, config, max_tokens=4096)
    return {
        "success": True,
        "content": content,
        "reasoning_content": reasoning_content,
        "papers": papers_info,
        "user_context": user_context or ""
    }


def add_idea_spark_session(papers_info, user_context, result_content, reasoning_content=None):
    """把一次 Idea Spark 会话写入历史"""
    data = load_idea_spark_history()
    session = {
        "id": str(int(time.time() * 1000)),
        "time": int(time.time()),
        "papers": papers_info,
        "user_context": user_context or "",
        "result": result_content,
        "reasoning_content": reasoning_content or ""
    }
    data["sessions"].insert(0, session)
    # 最多保留 50 条
    if len(data["sessions"]) > 50:
        data["sessions"] = data["sessions"][:50]
    save_idea_spark_history(data)
    return session


def get_idea_spark_session(session_id):
    """根据 id 获取单条会话"""
    data = load_idea_spark_history()
    for s in data.get("sessions", []):
        if s.get("id") == session_id:
            return s
    return None


def build_cc_project(session, target_dir):
    """Generate a self-contained Claude Code project directory from an Idea Spark session.

    Returns the Path to the created directory.
    """
    from datetime import datetime
    from shutil import copytree

    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    # brief.md
    (target / "brief.md").write_text(session.get("result", ""), encoding="utf-8")

    # selected-papers.json
    (target / "selected-papers.json").write_text(
        json.dumps(session.get("papers", []), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # CLAUDE.md
    claude_md = f"""# Project: Research Brief from WhiskerShelf

This project was generated by **WhiskerShelf's Idea Spark** feature on {datetime.fromtimestamp(session.get('time', 0)).strftime('%Y-%m-%d')}.
You are helping the user turn a research brief into executable work.

## Context
- The user selected {len(session.get('papers', []))} papers from their local WhiskerShelf library.
- `brief.md` contains the LLM-generated research directions.
- `selected-papers.json` has full paper metadata (titles, abstracts, tags, notes).

## Your role
You are a research collaborator, not just a code generator. Before writing code:
1. Read `brief.md` end to end
2. Identify which of the 3-5 directions the user wants to pursue
3. Propose a concrete plan (5-7 steps) and ask for confirmation
4. Then begin execution

## Available skills (auto-loaded)
- `whiskershelf-brief` — load and interpret the brief
- `whiskershelf-search` — query the user's local library
- `whiskershelf-tag` — organize papers with tags

## Conventions
- When implementing a direction from the brief, follow the "method transfer path" and "expected challenges" sections.
- When the user references "the X paper" or "my notes on Y", use `whiskershelf-search` to find it.
- After meaningful progress, suggest tags for the new artifact.
"""
    (target / "CLAUDE.md").write_text(claude_md, encoding="utf-8")

    # Starters
    (target / "start-claude.sh").write_text(
        "#!/usr/bin/env bash\necho \"Starting Claude Code with WhiskerShelf project context...\"\necho \"Tip: if 'claude' is not found, install: https://claude.com/code\"\nexec claude\n",
        encoding="utf-8"
    )
    (target / "start-claude.bat").write_text(
        "@echo off\r\necho Starting Claude Code with WhiskerShelf project context...\r\necho Tip: if 'claude' is not found, install: https://claude.com/code\r\nclaude\r\npause\r\n",
        encoding="utf-8"
    )

    # Copy Skill templates from the top-level whiskershelf-skills/ directory
    if SKILLS_DIR.exists():
        copytree(SKILLS_DIR, target / ".claude" / "skills")

    return target


class PaperHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # 简化日志，打印到控制台
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath, content_type):
        path = Path(filepath)
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        # Prevent browser from caching static files so code changes take effect on next refresh
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # API: 获取论文列表
        if path == "/api/papers":
            self._send_json(get_papers())
            return

        # API: 获取所有标签
        if path == "/api/tags":
            self._send_json(get_all_tags())
            return

        # API: 获取预设标签库
        if path == "/api/presets":
            self._send_json(load_presets())
            return

        # API: 获取AI配置（不返回API Key，只返回是否有Key）
        if path == "/api/ai/config":
            cfg = load_ai_config()
            safe = {
                "base_url": cfg.get("base_url", "https://api.deepseek.com/v1"),
                "model": cfg.get("model", "deepseek-chat"),
                "enabled": cfg.get("enabled", False),
                "has_key": bool(cfg.get("api_key", "").strip()),
                "thinking_enabled": cfg.get("thinking_enabled", False),
                "thinking_budget": cfg.get("thinking_budget", 2048),
                "cc_project_dir": cfg.get("cc_project_dir", "")
            }
            self._send_json(safe)
            return

        # API: Idea Spark 历史列表 /api/idea-spark/history
        if path == "/api/idea-spark/history":
            data = load_idea_spark_history()
            # 只返回摘要信息，不返回完整 result
            summary = []
            for s in data.get("sessions", []):
                papers = s.get("papers", [])
                paper_titles = [p.get("title") or p.get("name", "") for p in papers]
                preview = (s.get("result") or "")[:80].replace("\n", " ")
                summary.append({
                    "id": s.get("id"),
                    "time": s.get("time"),
                    "paper_titles": paper_titles,
                    "user_context": s.get("user_context", ""),
                    "preview": preview
                })
            self._send_json({"success": True, "sessions": summary})
            return

        # API: Idea Spark 单条历史 /api/idea-spark/history/{id}
        if path.startswith("/api/idea-spark/history/"):
            sid = path[len("/api/idea-spark/history/"):]
            if not sid:
                self._send_json({"error": "invalid id"}, 400)
                return
            session = get_idea_spark_session(sid)
            if not session:
                self._send_json({"error": "not found"}, 404)
                return
            self._send_json({"success": True, "session": session})
            return

        # API: AI 分析历史列表 /api/analysis/history
        if path == "/api/analysis/history":
            data = load_analysis_history()
            summary = []
            for s in data.get("sessions", []):
                preview = (s.get("analysis") or "")[:80].replace("\n", " ")
                summary.append({
                    "id": s.get("id"),
                    "time": s.get("time"),
                    "preview": preview,
                    "migrated": bool(s.get("migrated", False))
                })
            self._send_json({"success": True, "sessions": summary})
            return

        # API: AI 分析单条历史 /api/analysis/history/{id}
        if path.startswith("/api/analysis/history/"):
            sid = path[len("/api/analysis/history/"):]
            if not sid:
                self._send_json({"error": "invalid id"}, 400)
                return
            session = get_analysis_session(sid)
            if not session:
                self._send_json({"error": "not found"}, 404)
                return
            self._send_json({"success": True, "session": session})
            return

        # API: Agent - 列出所有论文 /api/agent/papers
        if path == "/api/agent/papers":
            papers = get_papers()
            summary = []
            for p in papers:
                ab = (p.get("abstract") or "").strip()
                summary.append({
                    "name": p.get("name"),
                    "title": p.get("display") or p.get("name"),
                    "tags": p.get("tags", []),
                    "abstract_preview": ab[:300]
                })
            self._send_json({"papers": summary})
            return

        # API: Agent - 单篇论文详情 /api/agent/papers/{name}
        if path.startswith("/api/agent/papers/"):
            if path.endswith("/tags"):
                # GET /api/agent/papers/{name}/tags — read tags
                name = urllib.parse.unquote(path[len("/api/agent/papers/"):-len("/tags")])
                if not name:
                    self._send_json({"error": "invalid name"}, 400)
                    return
                tags = load_tags()
                if name not in tags:
                    self._send_json({"error": "not found"}, 404)
                    return
                self._send_json({"tags": tags[name]})
                return
            # else: detail endpoint
            name = urllib.parse.unquote(path[len("/api/agent/papers/"):])
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            paper_map = {p["name"]: p for p in get_papers()}
            p = paper_map.get(name)
            if not p:
                self._send_json({"error": "not found"}, 404)
                return
            self._send_json({
                "name": name,
                "title": p.get("display") or name,
                "abstract": p.get("abstract", ""),
                "tags": p.get("tags", []),
                "notes": p.get("notes", "")
            })
            return

        # 静态文件 /static/...
        if path.startswith("/static/"):
            rel = path[8:]  # 去掉 /static/
            # 防止目录遍历
            target = (STATIC_DIR / rel).resolve()
            if not str(target).startswith(str(STATIC_DIR.resolve())):
                self.send_error(403)
                return
            # 猜测 Content-Type
            ext = target.suffix.lower()
            ctype = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".woff2": "font/woff2",
            }.get(ext, "application/octet-stream")
            self._send_file(target, ctype)
            return

        # 根路径 -> index.html
        if path == "/" or path == "/index.html":
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return

        # 直接访问 PDF（在当前目录）
        file_path = ROOT / path.lstrip("/")
        if file_path.exists() and file_path.is_file() and file_path.suffix.lower() == ".pdf":
            # 安全：确保在ROOT下
            try:
                resolved = file_path.resolve()
                if not str(resolved).startswith(str(ROOT)):
                    self.send_error(403)
                    return
            except Exception:
                self.send_error(403)
                return
            self._send_file(resolved, "application/pdf")
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # API: 保存AI配置 /api/ai/config
        if path == "/api/ai/config":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            cfg = load_ai_config()
            if "api_key" in payload:
                cfg["api_key"] = payload["api_key"].strip()
            if "base_url" in payload:
                cfg["base_url"] = payload["base_url"].strip().rstrip("/")
            if "model" in payload:
                cfg["model"] = payload["model"].strip()
            if "enabled" in payload:
                cfg["enabled"] = bool(payload["enabled"])
            if "thinking_enabled" in payload:
                cfg["thinking_enabled"] = bool(payload["thinking_enabled"])
            if "thinking_budget" in payload:
                try:
                    cfg["thinking_budget"] = max(256, min(32768, int(payload["thinking_budget"])))
                except (ValueError, TypeError):
                    pass
            if "cc_project_dir" in payload:
                cfg["cc_project_dir"] = str(payload["cc_project_dir"] or "").strip()
            save_ai_config(cfg)
            safe = {k: v for k, v in cfg.items()}
            if safe.get("api_key"):
                safe["api_key"] = safe["api_key"][:4] + "****"
            self._send_json({"success": True, "config": safe})
            return

        # API: AI语义搜索 /api/ai/search
        if path == "/api/ai/search":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            query = payload.get("query", "").strip()
            if not query:
                self._send_json({"error": "query is empty"}, 400)
                return
            cfg = load_ai_config()
            if not cfg.get("enabled") or not cfg.get("api_key"):
                self._send_json({"error": "AI未配置或已禁用"}, 400)
                return
            try:
                papers = get_papers()
                presets = load_presets()
                result = ai_semantic_search(query, papers, presets, cfg)
                self._send_json({"success": True, "results": result})
            except Exception as e:
                print(f"[AI Search Error] {e}")
                self._send_json({"error": str(e)}, 500)
            return

        # API: AI标签推荐 /api/ai/tags
        if path == "/api/ai/tags":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            title = payload.get("title", "").strip()
            abstract = payload.get("abstract", "").strip()
            if not title:
                self._send_json({"error": "title is empty"}, 400)
                return
            cfg = load_ai_config()
            if not cfg.get("enabled") or not cfg.get("api_key"):
                self._send_json({"error": "AI未配置或已禁用"}, 400)
                return
            try:
                presets = load_presets()
                result = ai_recommend_tags(title, abstract, presets, cfg)
                self._send_json({"success": True, "tags": result})
            except Exception as e:
                print(f"[AI Tags Error] {e}")
                self._send_json({"error": str(e)}, 500)
            return

        # API: AI阅读习惯分析 /api/ai/analyze-habits
        if path == "/api/ai/analyze-habits":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            recent_titles = payload.get("recent_titles", [])
            read_stats = payload.get("read_stats", [])
            cfg = load_ai_config()
            if not cfg.get("enabled") or not cfg.get("api_key"):
                self._send_json({"error": "AI未配置或已禁用"}, 400)
                return
            try:
                # 拼接用户信息
                recent_str = "\n".join(f"  - {t}" for t in recent_titles) if recent_titles else "  无"
                stats_lines = [f"  - {s['title']}（阅读{s['count']}次）" for s in read_stats]
                stats_str = "\n".join(stats_lines) if stats_lines else "  无"

                messages = [
                    {"role": "system", "content": (
                        "你是一位学术研究助手，擅长分析研究者的文献阅读习惯。"
                        "请根据用户提供的最近阅读文献和阅读次数记录，分析其阅读习惯、研究兴趣方向、"
                        "知识覆盖面，并给出有针对性的阅读建议（如补充哪些方向、哪些论文值得深入等）。"
                        "请用中文回答，格式清晰，分点阐述。"
                    )},
                    {"role": "user", "content": (
                        f"以下是我的阅读记录，请分析我的阅读习惯并给出建议：\n\n"
                        f"【最近阅读的论文】\n{recent_str}\n\n"
                        f"【阅读次数记录（仅阅读1次以上的论文）】\n{stats_str}"
                    )}
                ]
                result, _ = call_llm(messages, cfg, max_tokens=4096)
                session = add_analysis_session(result)
                self._send_json({"success": True, "analysis": result, "session_id": session["id"]})
            except Exception as e:
                print(f"[AI Analyze Error] {e}")
                self._send_json({"error": str(e)}, 500)
            return

        # API: 保存 AI 分析结果（用于前端一次性手动保存） /api/analysis/save
        if path == "/api/analysis/save":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            analysis = payload.get("analysis", "").strip()
            if not analysis:
                self._send_json({"error": "analysis is empty"}, 400)
                return
            session = add_analysis_session(analysis)
            self._send_json({"success": True, "session_id": session["id"]})
            return

        # API: 迁移 localStorage 老数据 /api/analysis/migrate
        if path == "/api/analysis/migrate":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            legacy = payload.get("legacy_entries", [])
            if not isinstance(legacy, list):
                self._send_json({"error": "legacy_entries must be list"}, 400)
                return
            data = load_analysis_history()
            existing_ids = {s.get("id") for s in data.get("sessions", [])}
            migrated = 0
            for item in legacy:
                if not isinstance(item, dict):
                    continue
                content = (item.get("content") or "").strip()
                t = item.get("time")
                if not content:
                    continue
                # 用原 time 生成 id（避免重复）；若已存在则跳过
                if t:
                    try:
                        sid = str(int(float(t) * 1000))
                    except (ValueError, TypeError):
                        sid = str(int(time.time() * 1000)) + f"_{migrated}"
                else:
                    sid = str(int(time.time() * 1000)) + f"_{migrated}"
                if sid in existing_ids:
                    continue
                sess = {
                    "id": sid,
                    "time": int(t) if t else int(time.time()),
                    "analysis": content,
                    "migrated": True
                }
                data["sessions"].append(sess)
                existing_ids.add(sid)
                migrated += 1
            # 按 time 倒序，最多保留 50 条
            data["sessions"].sort(key=lambda x: x.get("time", 0), reverse=True)
            if len(data["sessions"]) > 50:
                data["sessions"] = data["sessions"][:50]
            save_analysis_history(data)
            self._send_json({"success": True, "migrated": migrated, "total": len(data["sessions"])})
            return

        # API: 导出 Idea Spark 为 Claude Code 项目目录 /api/idea-spark/export-cc-project
        if path == "/api/idea-spark/export-cc-project":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            session_id = payload.get("session_id", "").strip()
            target_dir = (payload.get("target_dir") or "").strip()
            if not session_id:
                self._send_json({"error": "session_id is required"}, 400)
                return
            session = get_idea_spark_session(session_id)
            if not session:
                self._send_json({"error": "session not found"}, 404)
                return
            try:
                if not target_dir:
                    # Default: <用户配置>/whiskershelf-brief-YYYY-MM-DD-HHMM/
                    # 基础目录来自 ai_config.json 的 cc_project_dir 字段
                    base = get_default_cc_project_base()
                    timestamp = time.strftime("%Y-%m-%d-%H%M", time.localtime(session.get("time", time.time())))
                    target_dir = str(base / f"whiskershelf-brief-{timestamp}")
                target = Path(target_dir)
                target.mkdir(parents=True, exist_ok=True)
                result_path = build_cc_project(session, target)
                self._send_json({"success": True, "path": str(result_path)})
            except Exception as e:
                print(f"[Export CC Project Error] {e}")
                self._send_json({"error": str(e)}, 500)
            return

        # API: Agent - 设置论文标签（gated，CC 需在 SKILL 中要求用户确认） /api/agent/papers/{name}/tags
        if path.startswith("/api/agent/papers/") and path.endswith("/tags"):
            prefix = "/api/agent/papers/"
            suffix = "/tags"
            name = urllib.parse.unquote(path[len(prefix):-len(suffix)])
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            new_tags = payload.get("tags", [])
            if not isinstance(new_tags, list):
                self._send_json({"error": "tags must be list"}, 400)
                return
            # Clean: strip + dedup
            cleaned = []
            seen = set()
            for t in new_tags:
                if isinstance(t, str):
                    t = t.strip()
                    if t and t not in seen:
                        seen.add(t)
                        cleaned.append(t)
            tags = load_tags()
            if name not in tags:
                self._send_json({"error": "paper not found"}, 404)
                return
            tags[name] = cleaned
            save_tags(tags)
            # Audit log (printed to server console)
            print(f"[Agent API] tags updated for {name}: {cleaned}")
            self._send_json({"success": True, "tags": cleaned})
            return

        # API: Agent - 语义搜索 /api/agent/search
        if path == "/api/agent/search":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            query = payload.get("query", "").strip()
            if not query:
                self._send_json({"results": []})
                return
            # Fall back to simple substring match across title + tags + abstract
            # (We don't call LLM here to keep agent API zero-cost.)
            q = query.lower()
            results = []
            for p in get_papers():
                haystacks = [
                    (p.get("display") or "").lower(),
                    " ".join(p.get("tags", [])).lower(),
                    (p.get("abstract") or "").lower(),
                ]
                if any(q in h for h in haystacks):
                    results.append({
                        "name": p.get("name"),
                        "title": p.get("display") or p.get("name"),
                        "abstract_preview": (p.get("abstract") or "")[:300]
                    })
            # Cap at 20 results
            self._send_json({"results": results[:20]})
            return

        # API: Idea Spark 灵感碰撞 /api/idea-spark/generate
        if path == "/api/idea-spark/generate":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            paper_names = payload.get("papers", [])
            user_context = payload.get("user_context", "").strip()
            if not isinstance(paper_names, list) or len(paper_names) < 2 or len(paper_names) > 4:
                self._send_json({"error": "请选择 2-4 篇论文"}, 400)
                return
            cfg = load_ai_config()
            if not cfg.get("enabled") or not cfg.get("api_key"):
                self._send_json({"error": "AI未配置或已禁用"}, 400)
                return
            try:
                all_papers = get_papers()
                paper_map = {p["name"]: p for p in all_papers}
                papers_info = []
                missing = []
                for name in paper_names:
                    p = paper_map.get(name)
                    if not p:
                        missing.append(name)
                        continue
                    # 标题优先用 display（去后缀），若无摘要则尝试实时提取
                    title = p.get("display") or name
                    abstract = (p.get("abstract") or "").strip()
                    if not abstract:
                        # 尝试从 PDF 实时提取摘要
                        pdf_path = ROOT / name
                        if pdf_path.exists():
                            abstract = extract_abstract_from_pdf(pdf_path)
                            if abstract:
                                # 顺便写回 paper_abstracts.json，下次免抽
                                abstracts = load_abstracts()
                                abstracts[name] = abstract
                                save_abstracts(abstracts)
                    papers_info.append({
                        "name": name,
                        "title": title,
                        "abstract": abstract,
                        "tags": p.get("tags", []),
                        "notes": p.get("notes", "")
                    })
                if missing:
                    self._send_json({"error": f"以下论文不存在: {', '.join(missing)}"}, 404)
                    return
                result = ai_idea_spark(papers_info, user_context, cfg)
                # 写入历史（含思维链）
                session = add_idea_spark_session(
                    papers_info, user_context,
                    result["content"],
                    result.get("reasoning_content")
                )
                self._send_json({
                    "success": True,
                    "content": result["content"],
                    "reasoning_content": result.get("reasoning_content"),
                    "papers": papers_info,
                    "user_context": user_context,
                    "session_id": session["id"]
                })
            except Exception as e:
                print(f"[Idea Spark Error] {e}")
                self._send_json({"error": str(e)}, 500)
            return

        # API: 打开文献库文件夹 /api/open-folder
        if path == "/api/open-folder":
            try:
                import subprocess, platform
                system = platform.system()
                if system == "Windows":
                    os.startfile(str(ROOT))
                elif system == "Darwin":
                    subprocess.Popen(["open", str(ROOT)])
                else:
                    subprocess.Popen(["xdg-open", str(ROOT)])
                self._send_json({"success": True})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        # API: 用系统默认程序打开本地PDF /api/open/{name}
        if path.startswith("/api/open/"):
            name = path[len("/api/open/"):]
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            file_path = ROOT / name
            try:
                resolved = file_path.resolve()
                if not str(resolved).startswith(str(ROOT)) or not resolved.is_file() or resolved.suffix.lower() != ".pdf":
                    self._send_json({"error": "file not found or not pdf"}, 404)
                    return
            except Exception:
                self._send_json({"error": "invalid path"}, 403)
                return
            # 更新阅读记录
            reading = load_reading()
            if name not in reading:
                reading[name] = {"read_count": 0, "last_read": 0, "starred": False}
            reading[name]["read_count"] = reading[name].get("read_count", 0) + 1
            reading[name]["last_read"] = int(time.time())
            save_reading(reading)
            try:
                import subprocess, platform
                system = platform.system()
                if system == "Windows":
                    os.startfile(str(resolved))
                elif system == "Darwin":  # macOS
                    subprocess.Popen(["open", str(resolved)])
                else:  # Linux
                    subprocess.Popen(["xdg-open", str(resolved)])
                self._send_json({"success": True, "reading": reading[name]})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        # API: 更新预设标签库 /api/presets
        if path == "/api/presets":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return

            presets = load_presets()
            action = payload.get("action")
            if action == "add":
                new_tag = payload.get("tag", "").strip()
                if new_tag and new_tag not in presets:
                    presets.append(new_tag)
                    presets.sort(key=lambda x: x.lower())
                    save_presets(presets)
            elif action == "remove":
                rem = payload.get("tag", "").strip()
                if rem in presets:
                    presets.remove(rem)
                    save_presets(presets)
            elif action == "set":
                new_list = payload.get("presets", [])
                cleaned = []
                seen = set()
                for t in new_list:
                    if isinstance(t, str):
                        t = t.strip()
                        if t and t not in seen:
                            seen.add(t)
                            cleaned.append(t)
                cleaned.sort(key=lambda x: x.lower())
                save_presets(cleaned)
                presets = cleaned
            else:
                self._send_json({"error": "unknown action"}, 400)
                return
            self._send_json({"success": True, "presets": presets})
            return

        # API: 更新论文标签 /api/papers/{name}/tags
        if path.startswith("/api/papers/") and path.endswith("/tags"):
            # 提取文件名
            prefix = "/api/papers/"
            suffix = "/tags"
            name = path[len(prefix):-len(suffix)]
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return

            # 读取请求体
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return

            new_tags = payload.get("tags", [])
            if not isinstance(new_tags, list):
                self._send_json({"error": "tags must be list"}, 400)
                return

            # 清理标签
            cleaned = []
            for t in new_tags:
                if isinstance(t, str):
                    t = t.strip()
                    if t:
                        cleaned.append(t)
            # 去重保持顺序
            seen = set()
            unique = []
            for t in cleaned:
                if t not in seen:
                    seen.add(t)
                    unique.append(t)

            tags = load_tags()
            tags[name] = unique
            save_tags(tags)
            self._send_json({"success": True, "tags": unique})
            return

        # API: 更新论文摘要 /api/papers/{name}/abstract
        if path.startswith("/api/papers/") and path.endswith("/abstract"):
            prefix = "/api/papers/"
            suffix = "/abstract"
            name = path[len(prefix):-len(suffix)]
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            abstract = payload.get("abstract", "").strip()
            abstracts = load_abstracts()
            abstracts[name] = abstract
            save_abstracts(abstracts)
            self._send_json({"success": True, "abstract": abstract})
            return

        # API: 自动从PDF提取摘要 /api/papers/{name}/extract-abstract
        if path.startswith("/api/papers/") and path.endswith("/extract-abstract"):
            prefix = "/api/papers/"
            suffix = "/extract-abstract"
            name = path[len(prefix):-len(suffix)]
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            file_path = ROOT / name
            try:
                resolved = file_path.resolve()
                if not str(resolved).startswith(str(ROOT)) or not resolved.is_file() or resolved.suffix.lower() != ".pdf":
                    self._send_json({"error": "file not found or not pdf"}, 404)
                    return
            except Exception:
                self._send_json({"error": "invalid path"}, 403)
                return
            abstract = extract_abstract_from_pdf(resolved)
            if abstract:
                # 同时保存到json
                abstracts = load_abstracts()
                abstracts[name] = abstract
                save_abstracts(abstracts)
                self._send_json({"success": True, "abstract": abstract})
            else:
                self._send_json({"success": False, "abstract": "", "message": "未能从PDF中提取到摘要，请手动粘贴"})
            return

        # API: 记录打开阅读 /api/papers/{name}/reading
        if path.startswith("/api/papers/") and path.endswith("/reading"):
            prefix = "/api/papers/"
            suffix = "/reading"
            name = path[len(prefix):-len(suffix)]
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            reading = load_reading()
            if name not in reading:
                reading[name] = {"read_count": 0, "last_read": 0, "starred": False}
            reading[name]["read_count"] = reading[name].get("read_count", 0) + 1
            reading[name]["last_read"] = int(time.time())
            save_reading(reading)
            self._send_json({"success": True, "reading": reading[name]})
            return

        # API: 切换收藏星标 /api/papers/{name}/star
        if path.startswith("/api/papers/") and path.endswith("/star"):
            prefix = "/api/papers/"
            suffix = "/star"
            name = path[len(prefix):-len(suffix)]
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            reading = load_reading()
            if name not in reading:
                reading[name] = {"read_count": 0, "last_read": 0, "starred": False}
            reading[name]["starred"] = not reading[name].get("starred", False)
            save_reading(reading)
            self._send_json({"success": True, "starred": reading[name]["starred"]})
            return

        # API: 打开 PDF 所在文件夹并选中文件 /api/papers/{name}/reveal
        if path.startswith("/api/papers/") and path.endswith("/reveal"):
            prefix = "/api/papers/"
            suffix = "/reveal"
            name = path[len(prefix):-len(suffix)]
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            file_path = ROOT / name
            try:
                resolved = file_path.resolve()
                if not str(resolved).startswith(str(ROOT)) or not resolved.is_file() or resolved.suffix.lower() != ".pdf":
                    self._send_json({"error": "file not found or not pdf"}, 404)
                    return
            except Exception:
                self._send_json({"error": "invalid path"}, 403)
                return
            try:
                import subprocess, platform
                system = platform.system()
                if system == "Windows":
                    # /select, 高亮文件；注意逗号不能有空格
                    subprocess.Popen(['explorer', '/select,', str(resolved)])
                elif system == "Darwin":
                    subprocess.Popen(['open', '-R', str(resolved)])
                else:
                    # Linux 没有标准 reveal，只能打开父目录
                    subprocess.Popen(['xdg-open', str(resolved.parent)])
                self._send_json({"success": True})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        # API: 保存阅读笔记 /api/papers/{name}/notes
        if path.startswith("/api/papers/") and path.endswith("/notes"):
            prefix = "/api/papers/"
            suffix = "/notes"
            name = path[len(prefix):-len(suffix)]
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            note = payload.get("notes", "")
            all_notes = load_notes()
            all_notes[name] = note
            save_notes(all_notes)
            self._send_json({"success": True, "notes": note})
            return

        self.send_error(404)


def main():
    # 兼容 Windows 控制台编码
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    # 如果 tags/presets 文件不存在，初始化
    if not TAGS_FILE.exists():
        print("[INFO] 未找到 paper_tags.json，正在扫描 PDF 初始化...")
        load_tags()
        print(f"[INFO] 已初始化，共 {len(load_tags())} 篇论文")
    if not PRESETS_FILE.exists():
        print("[INFO] 未找到 tag_presets.json，正在初始化默认预设标签...")
        load_presets()
        print(f"[INFO] 预设标签库初始化完成")

    server = HTTPServer(("127.0.0.1", PORT), PaperHandler)
    print(f"[OK] 服务已启动: http://127.0.0.1:{PORT}")
    print("[TIP] 按 Ctrl+C 停止服务")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] 服务已停止")
        sys.exit(0)


if __name__ == "__main__":
    main()

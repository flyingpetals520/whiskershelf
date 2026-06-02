/* ========== 全局状态 ========== */
let allPapers = [];
let allTags = [];      // 所有已使用过的标签（用于标签页导航）
let allPresets = [];   // 预设标签库
let currentTag = '__all__';
let searchQuery = '';
let sortMode = null;   // null | 'mtime-desc' | 'mtime-asc' | 'alpha-asc' | 'alpha-desc'
let editingPaper = null;
let editingTags = [];
let showStarredOnly = false;

/* 随机辅助函数 */
const themes = ['theme-yellow', 'theme-pink', 'theme-blue', 'theme-green'];

/* ========== API ========== */
async function apiGet(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

async function apiPost(url, body) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

/* ========== 初始化 ========== */
async function init() {
    try {
        const [papers, tags, presets] = await Promise.all([
            apiGet('/api/papers'),
            apiGet('/api/tags'),
            apiGet('/api/presets')
        ]);
        allPapers = papers;
        allTags = tags;
        allPresets = presets;
        loadSettings();
        loadAiConfig();
        renderTabs();
        renderRecentReads();
        renderGrid();
        randomizeCatPosition();
    } catch (e) {
        console.error(e);
        showToast('加载失败，请刷新重试 😢');
    }
}

/* ================================================================
   🐈‍⬛ 猫咪垂直位置调节区 —— 每张猫图独立调
   ================================================================
   说明：每张猫图的姿态/高度不同，需要不同的 top 值才能正确"坐"在最近阅读框上。

   调节方法：
   - 修改下面的数字（单位 px，必须是负数）
   - 保存后刷新页面，hover 鼠标到猫身上可见当前 top 值
   - 越负 = 猫越靠上（远离阅读框）；越接近 0 = 猫越往下（与阅读框重叠多）

   参考基准：CSS 默认 top: -160px（适用于 150-160px 高的猫）
   - 真实猫高比 160px 矮：减小绝对值（如 -100）
   - 真实猫高比 160px 高：增大绝对值（如 -200）
   ================================================================ */
const CAT_TOP_OFFSETS = {
    'cat_src.png':   -52,   // ← 原黑猫，躺着伸尾巴（较扁，调小绝对值）
    'cat_src_1.png': -88,   // ← 新黑猫1（坐姿，较高）
    'cat_src_2.png': -82,   // ← 新黑猫2（坐姿，较高）
    'cat_src_3.png': -82,   // ← 新黑猫3（坐姿，较高）
};
/* ================================================================ */

/* 随机设置黑猫在"最近阅读"框上的水平位置和图片 */
function randomizeCatPosition() {
    const cat = document.querySelector('.cat-on-shelf');
    if (!cat) {
        console.warn('[Cat] .cat-on-shelf not found');
        return;
    }
    // 随机 right 值：2% ~ 82%，确保猫不会超出框右边界
    const randomRight = Math.floor(Math.random() * 81) + 2;
    cat.style.right = randomRight + '%';
    // 随机选择四张猫图片之一
    const catImages = ['cat_src.png', 'cat_src_1.png', 'cat_src_2.png', 'cat_src_3.png'];
    const randomIdx = Math.floor(Math.random() * catImages.length);
    const chosen = catImages[randomIdx];
    cat.src = '/static/' + chosen;
    // 用 top 属性（不是 marginTop！）控制垂直位置：
    // 负值 = 猫的顶部在父元素顶部之外 = 猫向上探出
    const topOffset = CAT_TOP_OFFSETS[chosen] !== undefined ? CAT_TOP_OFFSETS[chosen] : -160;
    cat.style.top = topOffset + 'px';
    // 调试用：鼠标悬停猫身上可看到当前使用的图片和偏移值
    cat.title = `图片: ${chosen} | top: ${topOffset}px | right: ${randomRight}%`;
    console.log('[Cat] randomized:', chosen, 'top=', topOffset, 'right=', randomRight + '%');
}

/* ========== 渲染标签导航 ========== */
function renderTabs() {
    const container = document.getElementById('tagTabs');
    const existing = Array.from(container.querySelectorAll('.tab-btn:not([data-tag="__all__"])'));
    existing.forEach(el => el.remove());

    allTags.forEach(tag => {
        const btn = document.createElement('button');
        btn.className = 'tab-btn';
        btn.dataset.tag = tag;
        btn.innerHTML = `<span class="tab-pin"></span>${escapeHtml(tag)}`;
        btn.addEventListener('click', () => switchTab(tag));
        container.appendChild(btn);
    });

    const allBtn = container.querySelector('[data-tag="__all__"]');
    if (allBtn) {
        allBtn.onclick = () => switchTab('__all__');
    }
}

function switchTab(tag) {
    currentTag = tag;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tag === tag);
    });
    renderGrid();
}

/* ========== 最近阅读 ========== */
function renderRecentReads() {
    const container = document.getElementById('recentReads');
    const list = document.getElementById('recentReadsList');
    const recent = allPapers
        .filter(p => p.last_read > 0)
        .sort((a, b) => b.last_read - a.last_read)
        .slice(0, 5);
    container.style.display = 'flex';
    if (recent.length === 0) {
        list.innerHTML = '<span class="recent-read-empty">点击论文 📖 阅读后，这里会出现最近读过的文献~</span>';
        return;
    }
    list.innerHTML = recent.map((p, i) =>
        `<span class="recent-read-item" data-idx="${i}" title="${escapeHtml(p.display)}">
            <span class="recent-read-star">${p.starred ? '⭐' : ''}</span>
            ${escapeHtml(p.display)}
        </span>`
    ).join('');
    list.querySelectorAll('.recent-read-item').forEach(el => {
        el.addEventListener('click', () => {
            const paper = recent[parseInt(el.dataset.idx)];
            openPaper(paper);
        });
    });
}

function openPaper(paper) {
    if (pdfOpenMode === 'system') {
        apiPost(`/api/open/${encodeURIComponent(paper.name)}`, {})
            .then(result => {
                paper.read_count = (paper.read_count || 0) + 1;
                paper.last_read = Math.floor(Date.now() / 1000);
                renderGrid();
                renderRecentReads();
                showToast('正在用系统默认程序打开...');
            })
            .catch(err => {
                console.error(err);
                showToast('打开失败，请检查PDF阅读器 😢');
            });
    } else {
        apiPost(`/api/papers/${encodeURIComponent(paper.name)}/reading`, {})
            .then(result => {
                paper.read_count = result.reading.read_count;
                paper.last_read = result.reading.last_read;
                renderGrid();
                renderRecentReads();
            })
            .catch(err => console.error(err));
        window.open(encodeURIComponent(paper.name), '_blank');
    }
}

/* ========== 排序逻辑 ========== */
const sortBtn = document.getElementById('sortBtn');

function cycleSort() {
    const modes = [null, 'mtime-desc', 'mtime-asc', 'alpha-asc', 'alpha-desc'];
    const idx = modes.indexOf(sortMode);
    sortMode = modes[(idx + 1) % modes.length];
    updateSortButton();
    renderGrid();
}

function updateSortButton() {
    const labels = {
        null: '🗂️ 默认排序',
        'mtime-desc': '🕐 最新优先',
        'mtime-asc': '📜 最早优先',
        'alpha-asc': '🔤 A → Z',
        'alpha-desc': '🔤 Z → A'
    };
    sortBtn.textContent = labels[sortMode];
    const rots = { null: '-0.8deg', 'mtime-desc': '0.8deg', 'mtime-asc': '-1.2deg', 'alpha-asc': '0.5deg', 'alpha-desc': '-0.5deg' };
    sortBtn.style.transform = `rotate(${rots[sortMode]})`;
}

sortBtn.addEventListener('click', cycleSort);

function formatDate(ts) {
    if (!ts) return '';
    const d = new Date(ts * 1000);
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

function timeAgo(timestamp) {
    if (!timestamp) return '未读';
    const now = Date.now();
    const diff = now - timestamp * 1000;
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) return '刚刚';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return minutes + '分钟前';
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return hours + '小时前';
    const days = Math.floor(hours / 24);
    if (days < 30) return days + '天前';
    const months = Math.floor(days / 30);
    if (months < 12) return months + '个月前';
    const years = Math.floor(days / 365);
    return years + '年前';
}

function createCard(paper, idx) {
    const div = document.createElement('div');
    div.className = `paper-card ${themes[idx % themes.length]}`;
    const rot = ((idx * 7 + 3) % 50 - 25) / 10;
    div.style.setProperty('--card-rot', `${rot}deg`);
    const tapeRot = ((idx * 13 + 5) % 60 - 30) / 10;

    // 标签区分预设和自定义
    const tagsHtml = paper.tags.map((t, i) => {
        const isPreset = allPresets.includes(t);
        const cls = isPreset ? 'sticker preset' : 'sticker custom';
        const rotStyle = `style="--sticker-rot:${((i * 17) % 40 - 20) / 10}deg"`;
        return `<span class="${cls}" ${rotStyle}>${escapeHtml(t)}</span>`;
    }).join('');

    const dateStr = formatDate(paper.mtime);
    const abstractHtml = paper.abstract
        ? `<div class="card-abstract">📝 ${escapeHtml(paper.abstract.substring(0, 120))}${paper.abstract.length > 120 ? '...' : ''}</div>`
        : '';
    const notesHtml = paper.notes
        ? `<div class="card-notes">📒 ${escapeHtml(paper.notes.substring(0, 80))}${paper.notes.length > 80 ? '...' : ''}</div>`
        : '';

    div.innerHTML = `
        <div class="tape" style="--tape-rot:${tapeRot}deg"></div>
        <div class="pin"></div>
        <div class="card-title" title="${escapeHtml(paper.display)}">${escapeHtml(paper.display)}</div>
        <div class="card-tags">${tagsHtml}</div>
        ${abstractHtml}
        ${notesHtml}
        <div class="card-mtime">📅 ${dateStr}</div>
        <div class="card-reading">
            <span class="reading-count" title="阅读次数">👁️ ${paper.read_count || 0}次</span>
            <span class="reading-time" title="上次阅读">${timeAgo(paper.last_read)}</span>
        </div>
        <div class="card-actions">
            <button class="btn-icon btn-star ${paper.starred ? 'starred' : ''}" data-action="star" title="${paper.starred ? '取消收藏' : '收藏'}">${paper.starred ? '⭐' : '☆'}</button>
            <button class="btn-icon" data-action="reveal" title="打开文件位置">📂</button>
            <button class="btn-icon" data-action="edit" title="编辑标签 (Ctrl+S)">🏷️</button>
            <button class="btn-icon" data-action="open" title="打开PDF">📖</button>
        </div>
    `;

    div.querySelector('[data-action="star"]').addEventListener('click', (e) => {
        e.stopPropagation();
        const btn = e.currentTarget;
        apiPost(`/api/papers/${encodeURIComponent(paper.name)}/star`, {})
            .then(result => {
                paper.starred = result.starred;
                btn.textContent = result.starred ? '⭐' : '☆';
                btn.classList.toggle('starred', result.starred);
                btn.title = result.starred ? '取消收藏' : '收藏';
                showToast(result.starred ? '已收藏 ⭐' : '已取消收藏');
            })
            .catch(err => {
                console.error(err);
                showToast('操作失败');
            });
    });

    div.querySelector('[data-action="edit"]').addEventListener('click', (e) => {
        e.stopPropagation();
        openEditModal(paper);
    });

    div.querySelector('[data-action="open"]').addEventListener('click', (e) => {
        e.stopPropagation();
        openPaper(paper);
    });

    div.querySelector('[data-action="reveal"]').addEventListener('click', (e) => {
        e.stopPropagation();
        apiPost(`/api/papers/${encodeURIComponent(paper.name)}/reveal`, {})
            .then(() => showToast('已打开文件位置 📂'))
            .catch(err => {
                console.error(err);
                showToast('打开文件位置失败：' + (err.message || ''));
            });
    });

    return div;
}

/* ========== 搜索 + AI语义搜索 ========== */
const searchInput = document.getElementById('searchInput');
const aiSearchBtn = document.getElementById('aiSearchBtn');

searchInput.addEventListener('input', (e) => {
    if (isAiSearchMode) {
        isAiSearchMode = false;
        aiSearchBtn.classList.remove('active');
        searchInput.placeholder = '搜索论文名称...';
    }
    searchQuery = e.target.value.trim().toLowerCase();
    renderGrid();
});

aiSearchBtn.addEventListener('click', async () => {
    const query = searchInput.value.trim();
    if (!query) {
        showToast('请先输入搜索内容');
        return;
    }
    if (!isAiSearchMode) {
        // 执行AI语义搜索
        aiSearchBtn.disabled = true;
        aiSearchBtn.innerHTML = '<span class="ai-loading"></span>搜索中';
        try {
            const result = await apiPost('/api/ai/search', { query });
            if (result.success && result.results && result.results.length > 0) {
                isAiSearchMode = true;
                aiSearchBtn.classList.add('active');
                searchInput.placeholder = '🔮 AI语义搜索中...';
                // 用AI返回的结果过滤
                const matchedNames = new Set(result.results);
                allPapers.forEach(p => {
                    p._aiMatch = matchedNames.has(p.name);
                });
                renderGrid();
                showToast(`AI找到 ${result.results.length} 篇相关论文 ✨`);
            } else {
                showToast('AI未找到相关论文');
            }
        } catch (e) {
            console.error(e);
            showToast('AI搜索失败：' + (e.message || '请检查配置'));
        } finally {
            aiSearchBtn.disabled = false;
            aiSearchBtn.textContent = '🤖 AI搜索';
        }
    } else {
        // 取消AI搜索模式
        isAiSearchMode = false;
        aiSearchBtn.classList.remove('active');
        searchInput.placeholder = '搜索论文名称...';
        searchQuery = searchInput.value.trim().toLowerCase();
        renderGrid();
    }
});

function renderGrid() {
    const grid = document.getElementById('paperGrid');
    const empty = document.getElementById('emptyState');
    grid.innerHTML = '';

    let filtered = allPapers.filter(p => {
        if (isAiSearchMode) {
            return p._aiMatch;
        }
        const matchSearch = !searchQuery || p.display.toLowerCase().includes(searchQuery);
        const matchTag = currentTag === '__all__' || p.tags.includes(currentTag);
        const matchStar = !showStarredOnly || p.starred;
        return matchSearch && matchTag && matchStar;
    });

    // 排序
    if (sortMode === 'mtime-desc') {
        filtered.sort((a, b) => b.mtime - a.mtime);
    } else if (sortMode === 'mtime-asc') {
        filtered.sort((a, b) => a.mtime - b.mtime);
    } else if (sortMode === 'alpha-asc') {
        filtered.sort((a, b) => a.display.localeCompare(b.display, 'zh-CN', { sensitivity: 'base' }));
    } else if (sortMode === 'alpha-desc') {
        filtered.sort((a, b) => b.display.localeCompare(a.display, 'zh-CN', { sensitivity: 'base' }));
    }

    if (filtered.length === 0) {
        empty.style.display = 'block';
        return;
    }
    empty.style.display = 'none';

    filtered.forEach((p, idx) => {
        const card = createCard(p, idx);
        grid.appendChild(card);
    });
}

/* ========== 编辑标签模态框 ========== */
const editModal = document.getElementById('editModal');
const modalPaperName = document.getElementById('modalPaperName');
const modalCurrentTags = document.getElementById('modalCurrentTags');
const presetTagsGrid = document.getElementById('presetTagsGrid');
const presetSearchInput = document.getElementById('presetSearchInput');
const newTagInput = document.getElementById('newTagInput');
const addTagBtn = document.getElementById('addTagBtn');
const paperAbstractInput = document.getElementById('paperAbstractInput');
const saveAbstractBtn = document.getElementById('saveAbstractBtn');
const extractAbstractBtn = document.getElementById('extractAbstractBtn');
const paperNotesInput = document.getElementById('paperNotesInput');

function openEditModal(paper) {
    editingPaper = paper;
    editingTags = [...paper.tags];
    modalPaperName.textContent = paper.display;
    presetSearchInput.value = '';
    newTagInput.value = '';
    paperAbstractInput.value = paper.abstract || '';
    paperNotesInput.value = paper.notes || '';
    renderEditModal();
    editModal.style.display = 'flex';
    requestAnimationFrame(() => editModal.classList.add('show'));
}

function closeEditModal() {
    editModal.classList.remove('show');
    setTimeout(() => {
        editModal.style.display = 'none';
        editingPaper = null;
        editingTags = [];
    }, 300);
}

function renderEditModal() {
    // 已选区
    if (editingTags.length === 0) {
        modalCurrentTags.innerHTML = '<div class="empty-hint">暂无标签，从右侧点击添加</div>';
    } else {
        modalCurrentTags.innerHTML = editingTags.map(t =>
            `<span class="sticker" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</span>`
        ).join('');
        modalCurrentTags.querySelectorAll('.sticker').forEach(el => {
            el.addEventListener('click', () => {
                const tag = el.dataset.tag;
                editingTags = editingTags.filter(x => x !== tag);
                renderEditModal();
            });
        });
    }

    // 可选预设区（带搜索过滤）
    const filter = presetSearchInput.value.trim().toLowerCase();
    const available = allPresets.filter(t => !editingTags.includes(t) &&
        (!filter || t.toLowerCase().includes(filter)));

    if (available.length === 0) {
        presetTagsGrid.innerHTML = '<div class="empty-hint">没有匹配的标签</div>';
    } else {
        presetTagsGrid.innerHTML = available.map(t =>
            `<span class="preset-tag" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</span>`
        ).join('');
        presetTagsGrid.querySelectorAll('.preset-tag').forEach(el => {
            el.addEventListener('click', () => {
                const tag = el.dataset.tag;
                if (!editingTags.includes(tag)) {
                    editingTags.push(tag);
                    renderEditModal();
                }
            });
        });
    }
}

presetSearchInput.addEventListener('input', renderEditModal);

function addCustomTag() {
    const val = newTagInput.value.trim();
    if (!val) return;
    if (!editingTags.includes(val)) {
        editingTags.push(val);
        if (!allTags.includes(val)) {
            allTags.push(val);
            allTags.sort((a, b) => a.localeCompare(b, 'zh-CN'));
            renderTabs();
        }
    }
    newTagInput.value = '';
    renderEditModal();
}

newTagInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addCustomTag();
});
addTagBtn.addEventListener('click', addCustomTag);

// 保存摘要
saveAbstractBtn.addEventListener('click', async () => {
    if (!editingPaper) return;
    const abstract = paperAbstractInput.value.trim();
    try {
        await apiPost(`/api/papers/${encodeURIComponent(editingPaper.name)}/abstract`, { abstract });
        editingPaper.abstract = abstract;
        // 同时更新 allPapers 中对应项的 abstract
        const p = allPapers.find(x => x.name === editingPaper.name);
        if (p) p.abstract = abstract;
        renderGrid();
        showToast('摘要保存成功！');
    } catch (e) {
        console.error(e);
        showToast('摘要保存失败');
    }
});

// 自动提取摘要
extractAbstractBtn.addEventListener('click', async () => {
    if (!editingPaper) return;
    extractAbstractBtn.disabled = true;
    extractAbstractBtn.textContent = '提取中...';
    try {
        const result = await apiPost(`/api/papers/${encodeURIComponent(editingPaper.name)}/extract-abstract`, {});
        if (result.success && result.abstract) {
            paperAbstractInput.value = result.abstract;
            editingPaper.abstract = result.abstract;
            const p = allPapers.find(x => x.name === editingPaper.name);
            if (p) p.abstract = result.abstract;
            renderGrid();
            showToast('摘要自动提取成功！✨');
        } else {
            showToast(result.message || '未能提取到摘要，请手动粘贴');
        }
    } catch (e) {
        console.error(e);
        showToast('提取失败：' + (e.message || '请检查PDF文件'));
    } finally {
        extractAbstractBtn.disabled = false;
        extractAbstractBtn.textContent = '📝 自动提取摘要';
    }
});

// AI推荐标签
document.getElementById('aiRecommendBtn').addEventListener('click', async () => {
    if (!editingPaper) return;
    const btn = document.getElementById('aiRecommendBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="ai-loading"></span>推荐中';
    try {
        const abstract = paperAbstractInput.value.trim();
        const result = await apiPost('/api/ai/tags', {
            title: editingPaper.display,
            abstract: abstract
        });
        if (result.success && result.tags && result.tags.length > 0) {
            result.tags.forEach(tag => {
                if (!editingTags.includes(tag)) {
                    editingTags.push(tag);
                }
            });
            renderEditModal();
            showToast(`AI推荐了 ${result.tags.length} 个标签 ✨`);
        } else {
            showToast('AI未推荐出标签');
        }
    } catch (e) {
        console.error(e);
        showToast('AI推荐失败：' + (e.message || '请检查配置'));
    } finally {
        btn.disabled = false;
        btn.textContent = '🤖 AI推荐';
    }
});

async function saveEditingPaper() {
    if (!editingPaper) return;
    const btn = document.getElementById('saveTagsBtn');
    if (btn.disabled) return;
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.innerHTML = '<span class="ai-loading"></span>保存中';
    try {
        const notes = paperNotesInput.value.trim();
        await Promise.all([
            apiPost(`/api/papers/${encodeURIComponent(editingPaper.name)}/tags`, {
                tags: editingTags
            }),
            apiPost(`/api/papers/${encodeURIComponent(editingPaper.name)}/notes`, {
                notes: notes
            })
        ]);
        editingPaper.tags = [...editingTags];
        editingPaper.notes = notes;
        const p = allPapers.find(x => x.name === editingPaper.name);
        if (p) {
            p.tags = [...editingTags];
            p.notes = notes;
        }
        const used = new Set();
        allPapers.forEach(p => p.tags.forEach(t => used.add(t)));
        allTags = Array.from(used).sort((a, b) => a.localeCompare(b, 'zh-CN'));
        renderTabs();
        renderGrid();
        closeEditModal();
        showToast('保存成功！✨');
    } catch (e) {
        console.error(e);
        showToast('保存失败，请重试 😢');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

document.getElementById('saveTagsBtn').addEventListener('click', saveEditingPaper);

document.getElementById('cancelBtn').addEventListener('click', closeEditModal);
editModal.addEventListener('click', (e) => {
    if (e.target === editModal) closeEditModal();
});

/* ========== 标签编辑 Ctrl+S 快捷键 ========== */
document.addEventListener('keydown', (e) => {
    // Ctrl+S (Windows/Linux) 或 Cmd+S (Mac)
    if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
        // 仅在编辑标签模态框打开时生效
        if (editModal.style.display === 'flex' && editingPaper) {
            e.preventDefault();
            e.stopPropagation();
            saveEditingPaper();
        }
    }
});

/* ========== 收藏筛选按钮 ========== */
const starFilterBtn = document.getElementById('starFilterBtn');
starFilterBtn.addEventListener('click', () => {
    showStarredOnly = !showStarredOnly;
    starFilterBtn.classList.toggle('active', showStarredOnly);
    starFilterBtn.textContent = showStarredOnly ? '⭐ 收藏' : '☆ 收藏';
    renderGrid();
});

/* ========== 主题切换 ========== */
const themeToggleBtn = document.getElementById('themeToggleBtn');
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    themeToggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
}
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('paperLibrary_theme', next);
}
themeToggleBtn.addEventListener('click', toggleTheme);
// 初始化主题
applyTheme(localStorage.getItem('paperLibrary_theme') || 'light');

/* ========== 打开文件夹 ========== */
document.getElementById('openFolderBtn').addEventListener('click', () => {
    apiPost('/api/open-folder', {})
        .then(() => showToast('正在打开文件夹...'))
        .catch(err => {
            console.error(err);
            showToast('打开文件夹失败');
        });
});

/* ========== AI阅读习惯分析 ========== */
const analysisModal = document.getElementById('analysisModal');
const analysisContent = document.getElementById('analysisContent');
const analysisHistoryList = document.getElementById('analysisHistoryList');
const ANALYSIS_HISTORY_KEY = 'paperLibrary_analysisHistory';
const ANALYSIS_MIGRATED_KEY = 'paperLibrary_analysisMigrated_v2';

let analysisHistoryCache = [];  // 内存缓存

async function fetchAnalysisHistory() {
    try {
        const data = await apiGet('/api/analysis/history');
        analysisHistoryCache = data.sessions || [];
        return analysisHistoryCache;
    } catch (e) {
        console.error('获取分析历史失败', e);
        return [];
    }
}

async function migrateAnalysisFromLocal() {
    if (localStorage.getItem(ANALYSIS_MIGRATED_KEY) === '1') return 0;
    let legacy = [];
    try {
        const raw = localStorage.getItem(ANALYSIS_HISTORY_KEY);
        if (raw) legacy = JSON.parse(raw);
    } catch (e) {
        legacy = [];
    }
    if (!Array.isArray(legacy) || legacy.length === 0) {
        localStorage.setItem(ANALYSIS_MIGRATED_KEY, '1');
        return 0;
    }
    // 仅传 content + time 字段
    const entries = legacy
        .filter(it => it && (it.content || it.analysis))
        .map(it => ({ time: it.time, content: it.content || it.analysis }));
    try {
        const result = await apiPost('/api/analysis/migrate', { legacy_entries: entries });
        localStorage.setItem(ANALYSIS_MIGRATED_KEY, '1');
        // 迁移成功后清除 localStorage 老数据
        try { localStorage.removeItem(ANALYSIS_HISTORY_KEY); } catch (e) {}
        return result.migrated || 0;
    } catch (e) {
        console.error('迁移失败', e);
        return 0;
    }
}

function renderAnalysisHistory() {
    if (analysisHistoryCache.length === 0) {
        analysisHistoryList.innerHTML = '<div class="analysis-history-empty">暂无历史记录</div>';
        return;
    }
    analysisHistoryList.innerHTML = analysisHistoryCache.map((item, i) => {
        const d = new Date(item.time * 1000);
        const label = d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' +
                      d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
        const mig = item.migrated ? ' ⬆' : '';
        return `<div class="analysis-history-item${i === 0 ? ' active' : ''}" data-id="${escapeHtml(item.id)}" title="${escapeHtml((item.preview || '').substring(0, 60))}">${label}${mig}</div>`;
    }).join('');
    analysisHistoryList.querySelectorAll('.analysis-history-item').forEach(el => {
        el.addEventListener('click', () => {
            const id = el.dataset.id;
            loadAnalysisHistoryItem(id);
        });
    });
}

async function loadAnalysisHistoryItem(id) {
    try {
        const data = await apiGet(`/api/analysis/history/${encodeURIComponent(id)}`);
        const session = data.session;
        analysisContent.innerHTML = `<div class="analysis-text">${renderMarkdown(session.analysis)}</div>`;
        analysisHistoryList.querySelectorAll('.analysis-history-item').forEach(x => x.classList.remove('active'));
        const activeEl = analysisHistoryList.querySelector(`[data-id="${id}"]`);
        if (activeEl) activeEl.classList.add('active');
    } catch (e) {
        showToast('加载历史失败');
    }
}

// 打开分析模态框：先做迁移，再加载服务端历史
document.getElementById('analyzeHabitsBtn').addEventListener('click', async () => {
    analysisModal.style.display = 'flex';
    requestAnimationFrame(() => analysisModal.classList.add('show'));
    analysisHistoryList.innerHTML = '<div class="analysis-history-empty">加载中...</div>';
    const migrated = await migrateAnalysisFromLocal();
    await fetchAnalysisHistory();
    renderAnalysisHistory();
    if (migrated > 0) {
        showToast(`已从浏览器缓存迁移 ${migrated} 条历史 ✨`);
    }
    if (analysisHistoryCache.length > 0) {
        await loadAnalysisHistoryItem(analysisHistoryCache[0].id);
    } else {
        analysisContent.innerHTML = '<div class="analysis-loading">暂无分析记录，点击下方"一键分析"开始</div>';
    }
});

// 一键分析按钮
document.getElementById('runAnalysisBtn').addEventListener('click', async () => {
    const btn = document.getElementById('runAnalysisBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="ai-loading"></span>分析中';
    const recentTitles = allPapers
        .filter(p => p.last_read > 0)
        .sort((a, b) => b.last_read - a.last_read)
        .slice(0, 5)
        .map(p => p.display);
    const readStats = allPapers
        .filter(p => p.read_count > 1)
        .sort((a, b) => b.read_count - a.read_count)
        .map(p => ({ title: p.display, count: p.read_count }));
    analysisContent.innerHTML = '<div class="analysis-loading">正在分析你的阅读习惯，请稍候...</div>';
    try {
        const result = await apiPost('/api/ai/analyze-habits', {
            recent_titles: recentTitles,
            read_stats: readStats
        });
        if (result.success && result.analysis) {
            analysisContent.innerHTML = `<div class="analysis-text">${renderMarkdown(result.analysis)}</div>`;
            // 刷新服务端历史
            await fetchAnalysisHistory();
            renderAnalysisHistory();
            // 高亮刚生成的这条
            if (result.session_id) {
                const newEl = analysisHistoryList.querySelector(`[data-id="${result.session_id}"]`);
                if (newEl) {
                    analysisHistoryList.querySelectorAll('.analysis-history-item').forEach(x => x.classList.remove('active'));
                    newEl.classList.add('active');
                }
            }
        } else {
            analysisContent.innerHTML = '<div class="analysis-loading">分析失败，请重试</div>';
        }
    } catch (e) {
        console.error(e);
        analysisContent.innerHTML = `<div class="analysis-loading">分析失败：${escapeHtml(e.message || '请检查AI配置')}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '🧠 一键分析';
    }
});

document.getElementById('closeAnalysisBtn').addEventListener('click', () => {
    analysisModal.classList.remove('show');
    setTimeout(() => { analysisModal.style.display = 'none'; }, 300);
});
analysisModal.addEventListener('click', (e) => {
    if (e.target === analysisModal) {
        analysisModal.classList.remove('show');
        setTimeout(() => { analysisModal.style.display = 'none'; }, 300);
    }
});

/* ========== Idea Spark 跨论文灵感碰撞 ========== */
const ideaSparkModal = document.getElementById('ideaSparkModal');
const ideaSparkHistoryList = document.getElementById('ideaSparkHistoryList');
const ideaSparkResult = document.getElementById('ideaSparkResult');
const ideaResultToolbar = document.getElementById('ideaResultToolbar');
const ideaPaperSearch = document.getElementById('ideaPaperSearch');
const ideaSelectedChips = document.getElementById('ideaSelectedChips');
const ideaPaperResults = document.getElementById('ideaPaperResults');
const ideaCounter = document.getElementById('ideaCounter');
const ideaUserContext = document.getElementById('ideaUserContext');
const runIdeaSparkBtn = document.getElementById('runIdeaSparkBtn');
const clearIdeaSparkBtn = document.getElementById('clearIdeaSparkBtn');
const closeIdeaSparkBtn = document.getElementById('closeIdeaSparkBtn');
const downloadMdBtn = document.getElementById('downloadMdBtn');
const copyMdBtn = document.getElementById('copyMdBtn');
const viewSourceBtn = document.getElementById('viewSourceBtn');
const sourceOverlay = document.getElementById('sourceOverlay');
const sourceEditor = document.getElementById('sourceEditor');
const applySourceBtn = document.getElementById('applySourceBtn');
const cancelSourceBtn = document.getElementById('cancelSourceBtn');
const ideaThinkingPanel = document.getElementById('ideaThinkingPanel');
const ideaThinkingContent = document.getElementById('ideaThinkingContent');
const ideaThinkingMeta = document.getElementById('ideaThinkingMeta');

function renderThinkingPanel() {
    if (ideaSparkCurrentReasoning && ideaSparkCurrentReasoning.trim()) {
        const len = ideaSparkCurrentReasoning.length;
        ideaThinkingContent.textContent = ideaSparkCurrentReasoning;
        ideaThinkingMeta.textContent = `(${len} 字)`;
        ideaThinkingPanel.style.display = 'block';
    } else {
        ideaThinkingPanel.style.display = 'none';
        ideaThinkingContent.textContent = '';
        ideaThinkingMeta.textContent = '';
    }
}

let ideaSparkSelected = [];
let ideaSparkCurrentSession = null;
let ideaSparkCurrentSource = '';
let ideaSparkCurrentReasoning = '';

const MAX_IDEA_PAPERS = 4;
const MIN_IDEA_PAPERS = 2;

function openIdeaSparkModal() {
    ideaSparkSelected = [];
    ideaSparkCurrentSession = null;
    ideaSparkCurrentSource = '';
    ideaSparkCurrentReasoning = '';
    ideaPaperSearch.value = '';
    ideaUserContext.value = '';
    ideaSparkResult.innerHTML = '<div class="analysis-loading">选择 2-4 篇论文后点击"✨ 火花碰撞!"开始</div>';
    ideaResultToolbar.style.display = 'none';
    renderThinkingPanel();
    renderIdeaSparkSelected();
    renderIdeaSparkResults();
    renderIdeaSparkHistory();
    ideaSparkModal.style.display = 'flex';
    requestAnimationFrame(() => ideaSparkModal.classList.add('show'));
}

function closeIdeaSparkModal() {
    ideaSparkModal.classList.remove('show');
    setTimeout(() => { ideaSparkModal.style.display = 'none'; }, 300);
}

function renderIdeaSparkSelected() {
    ideaCounter.textContent = `已选 ${ideaSparkSelected.length}/${MAX_IDEA_PAPERS}`;
    if (ideaSparkSelected.length === 0) {
        ideaSelectedChips.innerHTML = '<div class="empty-hint">还未选择论文，搜索名称或标签来添加</div>';
    } else {
        ideaSelectedChips.innerHTML = ideaSparkSelected.map(name => {
            const p = allPapers.find(x => x.name === name);
            const title = p ? p.display : name;
            const short = title.length > 32 ? title.substring(0, 32) + '…' : title;
            return `<span class="idea-paper-chip" data-name="${escapeHtml(name)}" title="${escapeHtml(title)}">
                ${escapeHtml(short)}
                <span class="idea-chip-remove">×</span>
            </span>`;
        }).join('');
        ideaSelectedChips.querySelectorAll('.idea-paper-chip').forEach(el => {
            el.addEventListener('click', () => {
                const name = el.dataset.name;
                ideaSparkSelected = ideaSparkSelected.filter(n => n !== name);
                renderIdeaSparkSelected();
                renderIdeaSparkResults();
            });
        });
    }
    updateRunBtnState();
}

function updateRunBtnState() {
    const ok = ideaSparkSelected.length >= MIN_IDEA_PAPERS && ideaSparkSelected.length <= MAX_IDEA_PAPERS;
    runIdeaSparkBtn.disabled = !ok;
    runIdeaSparkBtn.style.opacity = ok ? '1' : '0.5';
    runIdeaSparkBtn.style.cursor = ok ? 'pointer' : 'not-allowed';
}

function renderIdeaSparkResults() {
    const q = ideaPaperSearch.value.trim().toLowerCase();
    let filtered = allPapers.filter(p => !ideaSparkSelected.includes(p.name));
    if (q) {
        filtered = filtered.filter(p => {
            if (p.display.toLowerCase().includes(q)) return true;
            if (p.tags && p.tags.some(t => t.toLowerCase().includes(q))) return true;
            return false;
        });
    }
    filtered = filtered.slice(0, 30);
    if (filtered.length === 0) {
        ideaPaperResults.innerHTML = '<div class="empty-hint">没有匹配的论文</div>';
        return;
    }
    const atLimit = ideaSparkSelected.length >= MAX_IDEA_PAPERS;
    ideaPaperResults.innerHTML = filtered.map(p => {
        const tagBadges = (p.tags || []).slice(0, 3).map(t => `<span class="idea-mini-tag">${escapeHtml(t)}</span>`).join('');
        return `<div class="idea-paper-result${atLimit ? ' disabled' : ''}" data-name="${escapeHtml(p.name)}">
            <div class="idea-paper-result-main">
                <div class="idea-paper-result-title">${escapeHtml(p.display)}</div>
                <div class="idea-paper-result-tags">${tagBadges}</div>
            </div>
            <button class="btn-ai-recommend idea-add-btn" ${atLimit ? 'disabled' : ''}>${atLimit ? '已达上限' : '+ 添加'}</button>
        </div>`;
    }).join('');
    ideaPaperResults.querySelectorAll('.idea-paper-result').forEach(el => {
        el.addEventListener('click', (e) => {
            if (el.classList.contains('disabled')) return;
            const name = el.dataset.name;
            if (ideaSparkSelected.length >= MAX_IDEA_PAPERS) {
                showToast(`最多选择 ${MAX_IDEA_PAPERS} 篇`);
                return;
            }
            ideaSparkSelected.push(name);
            renderIdeaSparkSelected();
            renderIdeaSparkResults();
        });
    });
}

ideaPaperSearch.addEventListener('input', renderIdeaSparkResults);

runIdeaSparkBtn.addEventListener('click', async () => {
    if (ideaSparkSelected.length < MIN_IDEA_PAPERS) {
        showToast(`请至少选择 ${MIN_IDEA_PAPERS} 篇论文`);
        return;
    }
    runIdeaSparkBtn.disabled = true;
    runIdeaSparkBtn.innerHTML = '<span class="ai-loading"></span>碰撞中';
    ideaSparkResult.innerHTML = '<div class="analysis-loading">正在碰撞灵感，请稍候（可能需要 10-30 秒）...</div>';
    ideaResultToolbar.style.display = 'none';
    try {
        const result = await apiPost('/api/idea-spark/generate', {
            papers: ideaSparkSelected,
            user_context: ideaUserContext.value
        });
        if (result.success) {
            ideaSparkCurrentSource = result.content;
            ideaSparkCurrentReasoning = result.reasoning_content || '';
            ideaSparkResult.innerHTML = `<div class="analysis-text">${renderMarkdown(result.content)}</div>`;
            ideaResultToolbar.style.display = 'flex';
            renderThinkingPanel();
            ideaSparkCurrentSession = {
                id: result.session_id,
                papers: result.papers,
                user_context: result.user_context
            };
            renderIdeaSparkHistory();
            // 如果启用了思考但没拿到 reasoning_content，给个轻提示
            if (aiConfig.thinking_enabled && !ideaSparkCurrentReasoning) {
                showToast('提示：已开启思考但未获取到思维链，请确认模型支持（如 deepseek-reasoner、Qwen3-Thinking）');
            } else {
                showToast('灵感已生成 ✨');
            }
        } else {
            ideaSparkResult.innerHTML = `<div class="analysis-loading">生成失败：${escapeHtml(result.error || '未知错误')}</div>`;
        }
    } catch (e) {
        console.error(e);
        ideaSparkResult.innerHTML = `<div class="analysis-loading">生成失败：${escapeHtml(e.message || '请检查AI配置')}</div>`;
    } finally {
        runIdeaSparkBtn.innerHTML = '✨ 火花碰撞!';
        updateRunBtnState();
    }
});

clearIdeaSparkBtn.addEventListener('click', () => {
    ideaSparkSelected = [];
    ideaSparkCurrentSession = null;
    ideaSparkCurrentSource = '';
    ideaSparkCurrentReasoning = '';
    renderIdeaSparkSelected();
    renderIdeaSparkResults();
    ideaSparkResult.innerHTML = '<div class="analysis-loading">已清空，请重新选择论文</div>';
    ideaResultToolbar.style.display = 'none';
    renderThinkingPanel();
});

closeIdeaSparkBtn.addEventListener('click', closeIdeaSparkModal);
ideaSparkModal.addEventListener('click', (e) => {
    if (e.target === ideaSparkModal) closeIdeaSparkModal();
});

document.getElementById('ideaSparkBtn').addEventListener('click', openIdeaSparkModal);

function makeMdFilename() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `idea-spark-${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}.md`;
}

function buildFullMarkdown() {
    const time = new Date().toLocaleString('zh-CN');
    let papers = [];
    if (ideaSparkCurrentSession && ideaSparkCurrentSession.papers) {
        papers = ideaSparkCurrentSession.papers;
    } else {
        papers = ideaSparkSelected.map(n => {
            const p = allPapers.find(x => x.name === n);
            return { name: n, title: p ? p.display : n };
        });
    }
    const paperList = papers.map(p => `- ${p.title || p.name}`).join('\n');
    const ctx = ideaUserContext.value.trim() ? `\n## 补充背景\n${ideaUserContext.value.trim()}\n` : '';
    let thinking = '';
    if (ideaSparkCurrentReasoning && ideaSparkCurrentReasoning.trim()) {
        thinking = `\n## 模型的思考过程\n\n\`\`\`\n${ideaSparkCurrentReasoning}\n\`\`\`\n`;
    }
    return `# Idea Spark 灵感火花\n\n> 生成时间：${time}\n\n## 选中的论文\n${paperList}\n${ctx}${thinking}---\n\n${ideaSparkCurrentSource || ''}`;
}

downloadMdBtn.addEventListener('click', () => {
    if (!ideaSparkCurrentSource) return;
    const md = buildFullMarkdown();
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = makeMdFilename();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('已下载 .md 文件 📥');
});

copyMdBtn.addEventListener('click', async () => {
    if (!ideaSparkCurrentSource) return;
    const md = buildFullMarkdown();
    try {
        await navigator.clipboard.writeText(md);
        showToast('已复制到剪贴板 📋');
    } catch (e) {
        const ta = document.createElement('textarea');
        ta.value = md;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try {
            document.execCommand('copy');
            showToast('已复制到剪贴板 📋');
        } catch (e2) {
            showToast('复制失败，请手动选择');
        }
        document.body.removeChild(ta);
    }
});

viewSourceBtn.addEventListener('click', () => {
    if (!ideaSparkCurrentSource) return;
    sourceEditor.value = ideaSparkCurrentSource;
    sourceOverlay.style.display = 'flex';
    requestAnimationFrame(() => sourceOverlay.classList.add('show'));
});

applySourceBtn.addEventListener('click', () => {
    ideaSparkCurrentSource = sourceEditor.value;
    ideaSparkResult.innerHTML = `<div class="analysis-text">${renderMarkdown(ideaSparkCurrentSource)}</div>`;
    sourceOverlay.classList.remove('show');
    setTimeout(() => { sourceOverlay.style.display = 'none'; }, 300);
    showToast('已应用到结果');
});

cancelSourceBtn.addEventListener('click', () => {
    sourceOverlay.classList.remove('show');
    setTimeout(() => { sourceOverlay.style.display = 'none'; }, 300);
});

sourceOverlay.addEventListener('click', (e) => {
    if (e.target === sourceOverlay) {
        sourceOverlay.classList.remove('show');
        setTimeout(() => { sourceOverlay.style.display = 'none'; }, 300);
    }
});

async function renderIdeaSparkHistory() {
    try {
        const data = await apiGet('/api/idea-spark/history');
        const list = data.sessions || [];
        if (list.length === 0) {
            ideaSparkHistoryList.innerHTML = '<div class="analysis-history-empty">暂无历史</div>';
            return;
        }
        ideaSparkHistoryList.innerHTML = list.map(s => {
            const d = new Date(s.time * 1000);
            const label = d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' +
                          d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            const papersShort = s.paper_titles.slice(0, 2).join(' · ').substring(0, 22);
            const papersMore = s.paper_titles.length > 2 ? '…' : '';
            return `<div class="analysis-history-item" data-id="${escapeHtml(s.id)}" title="${escapeHtml(s.paper_titles.join(' | '))}">
                <div class="idea-history-label">${label}</div>
                <div class="idea-history-papers">${escapeHtml(papersShort)}${papersMore}</div>
            </div>`;
        }).join('');
        ideaSparkHistoryList.querySelectorAll('.analysis-history-item').forEach(el => {
            el.addEventListener('click', async () => {
                const id = el.dataset.id;
                ideaSparkHistoryList.querySelectorAll('.analysis-history-item').forEach(x => x.classList.remove('active'));
                el.classList.add('active');
                await loadIdeaSparkHistoryItem(id);
            });
        });
    } catch (e) {
        ideaSparkHistoryList.innerHTML = '<div class="analysis-history-empty">加载失败</div>';
    }
}

async function loadIdeaSparkHistoryItem(id) {
    try {
        const data = await apiGet(`/api/idea-spark/history/${encodeURIComponent(id)}`);
        const session = data.session;
        ideaSparkCurrentSource = session.result;
        ideaSparkCurrentReasoning = session.reasoning_content || '';
        ideaSparkResult.innerHTML = `<div class="analysis-text">${renderMarkdown(session.result)}</div>`;
        ideaResultToolbar.style.display = 'flex';
        renderThinkingPanel();
        ideaSparkCurrentSession = {
            id: session.id,
            papers: session.papers,
            user_context: session.user_context
        };
        ideaSparkSelected = (session.papers || []).map(p => p.name);
        ideaUserContext.value = session.user_context || '';
        renderIdeaSparkSelected();
        renderIdeaSparkResults();
        ideaSparkResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (e) {
        showToast('加载历史失败');
    }
}

/* ========== 刷新按钮 ========== */
document.getElementById('refreshBtn').addEventListener('click', async () => {
    const btn = document.getElementById('refreshBtn');
    btn.disabled = true;
    btn.textContent = '刷新中...';
    try {
        await init();
        showToast('文献列表已刷新 ✨');
    } catch (e) {
        showToast('刷新失败');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 刷新';
    }
});

/* ========== 设置模态框 ========== */
const settingsModal = document.getElementById('settingsModal');
const settingsBtn = document.getElementById('settingsBtn');
const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const pdfOpenRadios = document.querySelectorAll('input[name="pdfOpenMode"]');

let pdfOpenMode = 'browser'; // 'browser' | 'download'
let nickname = '';

function loadSettings() {
    try {
        const saved = localStorage.getItem('paperLibrary_settings');
        if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed.pdfOpenMode) {
                pdfOpenMode = parsed.pdfOpenMode;
                pdfOpenRadios.forEach(r => {
                    r.checked = (r.value === pdfOpenMode);
                });
            }
            if (parsed.nickname !== undefined) {
                nickname = parsed.nickname;
                document.getElementById('nicknameInput').value = nickname;
            }
        }
    } catch (e) {
        console.log('设置加载失败');
    }
    updateSiteTitle();
}

function saveSettings() {
    try {
        localStorage.setItem('paperLibrary_settings', JSON.stringify({
            pdfOpenMode: pdfOpenMode,
            nickname: nickname
        }));
    } catch (e) {
        console.log('设置保存失败');
    }
}

function updateSiteTitle() {
    const title = document.querySelector('.site-title');
    if (nickname.trim()) {
        title.textContent = `📚 ${nickname.trim()}的温馨文献库`;
    } else {
        title.textContent = '📚 我的温馨文献库';
    }
}

function openSettingsModal() {
    loadSettings();
    settingsModal.style.display = 'flex';
    requestAnimationFrame(() => settingsModal.classList.add('show'));
}

function closeSettingsModal() {
    settingsModal.classList.remove('show');
    setTimeout(() => {
        settingsModal.style.display = 'none';
    }, 300);
}

settingsBtn.addEventListener('click', openSettingsModal);
closeSettingsBtn.addEventListener('click', closeSettingsModal);
settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) closeSettingsModal();
});

pdfOpenRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.checked) {
            pdfOpenMode = e.target.value;
            saveSettings();
        }
    });
});

document.getElementById('nicknameInput').addEventListener('input', (e) => {
    nickname = e.target.value;
    saveSettings();
    updateSiteTitle();
});

// ==================== AI 配置 ====================
const AI_KEY_STORAGE = 'paperLibrary_aiKey';
let aiConfig = { api_key: '', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat', enabled: false };
let isAiSearchMode = false;

function loadAiKeyFromStorage() {
    try {
        return localStorage.getItem(AI_KEY_STORAGE) || '';
    } catch (e) {
        return '';
    }
}

function saveAiKeyToStorage(key) {
    try {
        localStorage.setItem(AI_KEY_STORAGE, key);
    } catch (e) {
        console.log('localStorage保存失败');
    }
}

async function loadAiConfig() {
    try {
        const cfg = await apiGet('/api/ai/config');
        // 从localStorage读取真实的API Key
        const realKey = loadAiKeyFromStorage();
        aiConfig = {
            api_key: realKey,
            base_url: cfg.base_url || 'https://api.deepseek.com/v1',
            model: cfg.model || 'deepseek-chat',
            enabled: cfg.enabled || false,
            thinking_enabled: cfg.thinking_enabled || false,
            thinking_budget: cfg.thinking_budget || 2048
        };
        document.getElementById('aiEnabled').checked = aiConfig.enabled;
        document.getElementById('aiApiKey').value = realKey;
        document.getElementById('aiBaseUrl').value = aiConfig.base_url;
        document.getElementById('aiModel').value = aiConfig.model;
        document.getElementById('aiThinkingEnabled').checked = aiConfig.thinking_enabled;
        document.getElementById('aiThinkingBudget').value = aiConfig.thinking_budget;
        updateThinkingBudgetVisibility();
        updateAiSearchButton();
    } catch (e) {
        console.log('AI配置加载失败');
    }
}

function updateThinkingBudgetVisibility() {
    const enabled = document.getElementById('aiThinkingEnabled').checked;
    document.getElementById('thinkingBudgetRow').style.display = enabled ? 'flex' : 'none';
}

async function saveAiConfig() {
    const key = document.getElementById('aiApiKey').value.trim();
    const cfg = {
        api_key: key,
        base_url: document.getElementById('aiBaseUrl').value.trim(),
        model: document.getElementById('aiModel').value.trim(),
        enabled: document.getElementById('aiEnabled').checked,
        thinking_enabled: document.getElementById('aiThinkingEnabled').checked,
        thinking_budget: parseInt(document.getElementById('aiThinkingBudget').value, 10) || 2048
    };
    try {
        await apiPost('/api/ai/config', cfg);
        saveAiKeyToStorage(key);
        aiConfig = cfg;
        showToast('AI配置已保存');
        updateAiSearchButton();
    } catch (e) {
        showToast('保存失败');
    }
}

function updateAiSearchButton() {
    const btn = document.getElementById('aiSearchBtn');
    if (aiConfig.enabled && aiConfig.api_key) {
        btn.style.display = 'inline-block';
    } else {
        btn.style.display = 'none';
        isAiSearchMode = false;
        btn.classList.remove('active');
        searchInput.placeholder = '搜索论文名称...';
    }
}

document.getElementById('aiEnabled').addEventListener('change', saveAiConfig);
document.getElementById('aiApiKey').addEventListener('change', saveAiConfig);
document.getElementById('aiBaseUrl').addEventListener('change', saveAiConfig);
document.getElementById('aiModel').addEventListener('change', saveAiConfig);
document.getElementById('aiThinkingEnabled').addEventListener('change', () => {
    updateThinkingBudgetVisibility();
    saveAiConfig();
});
document.getElementById('aiThinkingBudget').addEventListener('change', saveAiConfig);

document.getElementById('testAiBtn').addEventListener('click', async () => {
    const btn = document.getElementById('testAiBtn');
    btn.disabled = true;
    btn.textContent = '测试中...';
    try {
        await saveAiConfig();
        const cfg = await apiGet('/api/ai/config');
        if (cfg.enabled && cfg.api_key) {
            showToast('配置已保存，快去试试AI功能吧！');
        } else {
            showToast('请先填写API Key并启用AI');
        }
    } catch (e) {
        showToast('测试失败');
    } finally {
        btn.disabled = false;
        btn.textContent = '🧪 测试连接';
    }
});

/* ========== 管理预设标签模态框 ========== */
const presetsModal = document.getElementById('presetsModal');
const presetList = document.getElementById('presetList');
const newPresetInput = document.getElementById('newPresetInput');
const addPresetBtn = document.getElementById('addPresetBtn');
const managePresetsBtn = document.getElementById('managePresetsBtn');
const closePresetsBtn = document.getElementById('closePresetsBtn');

function openPresetsModal() {
    renderPresetList();
    newPresetInput.value = '';
    presetsModal.style.display = 'flex';
    requestAnimationFrame(() => presetsModal.classList.add('show'));
}

function closePresetsModal() {
    presetsModal.classList.remove('show');
    setTimeout(() => {
        presetsModal.style.display = 'none';
    }, 300);
}

function renderPresetList() {
    if (allPresets.length === 0) {
        presetList.innerHTML = '<div class="empty-hint">标签库为空，请添加标签</div>';
        return;
    }
    presetList.innerHTML = allPresets.map(t => `
        <div class="preset-list-item">
            <span>${escapeHtml(t)}</span>
            <span class="del-btn" data-tag="${escapeHtml(t)}">×</span>
        </div>
    `).join('');

    presetList.querySelectorAll('.del-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const tag = btn.dataset.tag;
            try {
                await apiPost('/api/presets', { action: 'remove', tag });
                allPresets = allPresets.filter(x => x !== tag);
                renderPresetList();
                showToast('已删除预设标签');
            } catch (e) {
                showToast('删除失败');
            }
        });
    });
}

async function addNewPreset() {
    const val = newPresetInput.value.trim();
    if (!val) return;
    if (allPresets.includes(val)) {
        showToast('该标签已存在');
        return;
    }
    try {
        await apiPost('/api/presets', { action: 'add', tag: val });
        allPresets.push(val);
        allPresets.sort((a, b) => a.localeCompare(b, 'zh-CN'));
        renderPresetList();
        newPresetInput.value = '';
        showToast('新标签已添加');
    } catch (e) {
        showToast('添加失败');
    }
}

newPresetInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addNewPreset();
});
addPresetBtn.addEventListener('click', addNewPreset);

managePresetsBtn.addEventListener('click', openPresetsModal);
closePresetsBtn.addEventListener('click', closePresetsModal);
presetsModal.addEventListener('click', (e) => {
    if (e.target === presetsModal) closePresetsModal();
});

/* ========== Toast ========== */
function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}

/* ========== 工具函数 ========== */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderMarkdown(text) {
    let html = escapeHtml(text);
    // 代码块 ```...```
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    // 行内代码 `...`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // 标题 ### / ## / #
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
    // 粗体 **...**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // 斜体 *...*
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // 无序列表 - 或 *
    html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/((<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
    // 有序列表 1. 2. etc
    html = html.replace(/^\d+\. (.+)$/gm, '<oli>$1</oli>');
    html = html.replace(/((<oli>.*<\/oli>\n?)+)/g, function(m) {
        return '<ol>' + m.replace(/<\/?oli>/g, function(t) {
            return t.replace('oli', 'li');
        }) + '</ol>';
    });
    // 分隔线 ---
    html = html.replace(/^---$/gm, '<hr>');
    // 段落：连续两个换行
    html = html.replace(/\n\n+/g, '</p><p>');
    // 单换行
    html = html.replace(/\n/g, '<br>');
    // 清理多余的 <br> 在块元素前后
    html = html.replace(/<br><(h[2-4]|ul|ol|pre|hr|li)/g, '<$1');
    html = html.replace(/<\/(h[2-4]|ul|ol|pre|li)><br>/g, '</$1>');
    return '<p>' + html + '</p>';
}

/* ========== 折纸小人气泡对话 ========== */
const bubbleQuotes = [
    "今天也要加油鸭！",
    "这篇论文看起来很有趣~",
    "记得休息一下眼睛哦 👀",
    "知识就是力量！",
    "你已经很棒啦 ✨",
    "读论文使我快乐（真的）",
    "这个标签打得真不错~",
    "坚持就是胜利！",
    "咖啡还是茶？☕",
    "别卷了，出去走走吧 🌿",
    "学术使我快乐，真的 😊",
    "又读完一篇，奖励自己一下！",
    "这个idea真不错，记下来！",
    "文献库越来越丰富啦~",
    "保持好奇，保持热爱 🔥"
];

const dollWrapper = document.getElementById('dollWrapper');
const speechBubble = document.getElementById('speechBubble');
const bubbleText = document.getElementById('bubbleText');

function pickRandomQuote() {
    const idx = Math.floor(Math.random() * bubbleQuotes.length);
    return bubbleQuotes[idx];
}

if (dollWrapper && speechBubble) {
    dollWrapper.addEventListener('mouseenter', () => {
        bubbleText.textContent = pickRandomQuote();
        speechBubble.classList.add('show');
    });
    dollWrapper.addEventListener('mouseleave', () => {
        speechBubble.classList.remove('show');
    });
}

/* ========== 回顶按钮 ========== */
const backToTopBtn = document.getElementById('backToTopBtn');

function toggleBackToTop() {
    if (window.scrollY > 300) {
        backToTopBtn.classList.add('show');
    } else {
        backToTopBtn.classList.remove('show');
    }
}

window.addEventListener('scroll', toggleBackToTop);

backToTopBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

/* 启动 */
init();

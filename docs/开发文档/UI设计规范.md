# 界面设计规范

> 本规范适用于「流程回归工作台」桌面应用（PySide6 / Qt）。所有新增或修改的 UI 代码必须遵守本文档。

---

## 一、设计哲学

**克制、精确、可预期。**

工具类软件的界面不是艺术品。每一个视觉元素都必须承载操作意义——否则就是噪音。

用户拿到这个工具，应该在 **30 秒内**找到他要的操作。如果找不到，是界面设计的问题，不是文档的问题。

---

## 二、布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  工具栏 Toolbar（40px，可隐藏）                                    │
│  全局操作：运行 / 暂停 / 停止                                      │
├────────────┬──────────────────────────────────┬─────────────────┤
│            │                                  │                 │
│  左侧导航栏  │       中央主操作区                │   右侧详情面板   │
│  240px     │       flex (min 680px)          │   300px         │
│            │                                  │                 │
│  · 品牌标识  │  · 页面标题 + 操作按钮           │  · 环境状态     │
│  · 环境指示  │  · Hero 引导区                  │  · 会话池策略   │
│  · 导航菜单  │  · 指标网格                      │  · 下一步指引   │
│            │  · 分段表单卡片                   │                 │
│            │  · （可滚动）                     │                 │
├────────────┴──────────────────────────────────┴─────────────────┤
│  状态栏 Status Bar（28px）                                        │
│  环境名称 | API 网关 | 连接状态                                    │
└─────────────────────────────────────────────────────────────────┘
```

**规则：**
- 三个面板宽度固定，不随内容缩放
- 左侧导航和右侧详情面板始终可见，中央区域可独立滚动
- 工具栏和状态栏固定高度，不参与滚动

---

## 三、色彩系统

### 3.1 基础色板

| 角色 | 色值 | 用途 |
|------|------|------|
| 背景 | `#f1f5f9` | 主窗口背景、中央内容区背景 |
| 表面（白卡） | `#ffffff` | 卡片、输入框、按钮背景 |
| 面板（浅灰） | `#f8fafc` | 右侧详情面板背景、节点规则背景 |
| 导航栏 | `#ffffff` | 左侧导航背景 |
| 边框 | `#e2e8f0` | 所有卡片、面板、分隔线默认状态 |
| 边框悬停 | `#94a3b8` | 输入框、按钮悬停时的边框 |

### 3.2 文字色板

| 层级 | 色值 | 用途 |
|------|------|------|
| 主文字 | `#0f172a` | 标题、数字、标签 |
| 正文 | `#1e293b` | 正文内容 |
| 次要文字 | `#475569` | 正文辅助、按钮文字 |
| 描述文字 | `#64748b` | 说明文字、元信息 |
| 占位文字 | `#94a3b8` | 页脚、空状态 |

### 3.3 Accent 色（品牌蓝）

所有主按钮、选中态、强调内容统一使用：

| 状态 | 色值 |
|------|------|
| 默认 | `#1e40af` |
| 悬停 | `#1e3a8a` |
| 按下 | `#1d3a9a` |
| 选中背景 | `#eff6ff` |
| 选中文字 | `#1e40af` |

### 3.4 状态色

状态色用于指示真实系统状态，**永远同时配图标或文字**，色盲用户不能靠颜色区分状态：

| 状态 | 色值 | 用途 |
|------|------|------|
| 成功 / 已完成 | `#22c55e` | 连接正常、步骤完成 |
| 失败 / 错误 | `#ef4444` | 连接失败、任务失败 |
| 警告 / 未配置 | `#fbbf24` | 缺少密钥、待查询 |
| 中性 / 待处理 | `#9ca3af` | 未经检查、跳过 |

### 3.5 禁止事项

- 禁止使用 `qlineargradient` 做背景（导致"卡通感"）
- 禁止在状态指示上**仅**用颜色区分（必须配合图标或文字）
- 禁止一个区域超过两种颜色叠加
- 禁止圆角超过 `10px`（纯色平面设计不需要夸张圆角）
- 禁止 drop shadow（`QGraphicsDropShadowEffect`）用于常规卡片

---

## 四、字体与字号

### 字号（仅两种）

| 用途 | 字号 |
|------|------|
| 正文、标签、描述 | `13px` |
| 辅助信息、时间戳、页脚 | `11px` |

例外（可在组件内单独定义）：
- Hero 标题：`22px`
- 指标数字：`20px`
- 页面标题：`14px`（Section Title）

### 字重（仅两档）

| 用途 | 字重 |
|------|------|
| 正文 | `400`（默认） |
| 强调（标题、标签、数值） | `600` |

**禁止使用 `700` 和 `900`**。粗体在工具类软件里是视觉噪音。

### 等宽字体

仅用于以下场景：API URL、JSON、日志行、路径。

```
font-family: "JetBrains Mono", "Fira Code", "SF Mono", Consolas, monospace;
```

其余全部使用系统无衬线字体：

```
font-family: "PingFang SC", "Helvetica Neue", sans-serif;
```

---

## 五、组件规范

### 5.1 品牌标识

- 用 `BrandIcon`（`QWidget` + `QPainter`）绘制：纯色方形背景 + 两条白色横线
- 尺寸：`32×32px`，圆角 `6px`
- 颜色：`#3b4fbd`（品牌蓝）
- **禁止使用 emoji 或中文汉字**作为品牌图

### 5.2 按钮

#### 主按钮（Primary）
```
background: #1e40af; color: #ffffff;
border: none; border-radius: 6px;
padding: 8px 16px; font-size: 13px; font-weight: 500;
```
悬停：`#1e3a8a`，按下：`#1d3a9a`

#### 次要按钮（Secondary）
```
background: #ffffff; color: #475569;
border: 1px solid #cbd5e1; border-radius: 6px;
padding: 8px 16px; font-size: 13px; font-weight: 500;
```
悬停：`background: #f8fafc; border-color: #94a3b8`

#### 导航按钮
```
text-align: left; padding: 8px 10px; font-size: 13px;
color: #475569; background: transparent; border: none;
border-radius: 6px;
```
选中：`color: #1e40af; background: #eff6ff; font-weight: 500;`

**规则：同一个操作区域内，主按钮只出现一个。**

### 5.3 卡片（Section Card）

所有内容卡片统一外观：
```
background: #ffffff;
border: 1px solid #e2e8f0;
border-radius: 8px;
```

顶部不要色条。层次感通过边框和阴影区分，不是靠颜色。

### 5.4 指标卡（Metric Card）

与 Section Card 相同的白色边框卡片，内部分栏：
- 标签：`11px`，`#64748b`
- 数值：`20px`，`#0f172a`，`font-weight: 600`
- 提示：`11px`，`#94a3b8`

### 5.5 节点规则行（Node Rule）

```
background: #f8fafc;
border: 1px solid #e2e8f0;
border-radius: 6px;
padding: 10px 12px;
```
左侧有 `8×8px` 蓝色状态点。

### 5.6 流程阶段追踪器（Stage Tracker）

放在 Hero 面板右侧，深色半透明背景：
```
background: rgba(255, 255, 255, 0.08);
border-radius: 8px;
```
阶段标记：已完成的用 ✓，当前激活的用 ●，未完成的用 ○。

### 5.7 标签（Chip）

```
font-size: 11px; font-weight: 500;
color: #3b82f6;
background: #eff6ff;
border: 1px solid #bfdbfe;
border-radius: 4px;
padding: 3px 8px;
```

### 5.8 输入框与下拉框

```
background: #ffffff;
border: 1px solid #cbd5e1;
border-radius: 6px;
padding: 7px 10px;
font-size: 13px; color: #0f172a;
```
悬停：`border-color: #94a3b8`
聚焦：`border-color: #3b82f6`

**规则：标签始终在输入框上方，不允许用 placeholder 替代标签。**

### 5.9 状态指示点

`StatusDot` 组件：`8×8px`，圆角 `4px`。
每种状态对应一种颜色（见 3.4），且必须同时有文字说明。

---

## 六、交互规范

### 6.1 键盘快捷键

| 快捷键 | 操作 |
|--------|------|
| `Space` | 全局暂停 / 恢复 |
| `F5` | 运行 |
| `Esc` | 停止 |
| `Ctrl+L` | 清空日志 |
| `Ctrl+E` | 导出报告 |

快捷键列表在帮助菜单中完整展示。

### 6.2 操作反馈

- 按钮点击后 **100ms 内**必须有视觉变化（状态改变或 loading）
- 超过 **500ms** 的操作显示进度指示
- 超过 **3 秒**的操作必须允许取消
- 禁止用户对着无反应的界面等待

### 6.3 破坏性操作确认

停止任务、清空日志、删除配置，弹出确认对话框，**取消按钮作为默认焦点**。

### 6.4 滚动行为

日志列表自动滚动到底部；如果用户手动向上滚动，停止自动滚动，底部显示浮动提示"↓ N 条新日志"，点击后恢复。

---

## 七、Qt CSS 限制

Qt Stylesheet 是 CSS 2.1 的子集，以下特性**不支持**，禁止使用：

| 特性 | 示例 | 替代方案 |
|------|------|----------|
| 子选择器 `>` | `QWidget#id > QLabel` | 用 `objectName` 属性选择器 |
| `:first-child` / `:not()` | `QPushButton:first-child` | 给子元素分别设置 `objectName` |
| `letter-spacing` | `letter-spacing: 0.05em` | 不支持，直接不用 |
| `text-transform` | `text-transform: uppercase` | 不支持，直接写小写或手动大写 |
| `::dropDown` / `::down-arrow` | QComboBox 子控件样式 | 简化，不定义下拉箭头样式 |
| 动画 `transition` | `transition: all 0.2s` | 使用 `QPropertyAnimation` 或不用 |

**推荐的选择器写法：**
- `QWidget#objectName` — 按对象名（唯一标识）
- `QLabel[objectName="name"]` — 属性选择器（精确匹配）
- `QLabel[objectName^="prefix"]` — 前缀匹配（同一类元素）

---

## 八、状态持久化

以下用户偏好必须持久化到本地，下次启动时恢复：

- 窗口大小和位置
- 左侧导航栏折叠状态
- 上次执行的配置（并发数、延迟、选中的流程）

---

## 九、检查清单

每次 UI 改动上线前自检：

- [ ] 没有使用 `qlineargradient` 做背景
- [ ] 状态指示同时有颜色 + 文字/图标
- [ ] 没有使用 `font-weight: 700` 或 `900`
- [ ] 没有使用 `border-radius: 20px` 以上的圆角
- [ ] 没有使用 `QGraphicsDropShadowEffect` 在常规卡片上
- [ ] Qt CSS 只用了属性选择器和 ID 选择器
- [ ] 标签在输入框上方，没有 placeholder 替代标签
- [ ] 主按钮区域内只有一个
- [ ] 破坏性操作有确认对话框

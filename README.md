# SkillCere

SkillCere（技能小脑）是一个跨 Agent 的 skill 清单管理与推荐上下文系统，用于持续发现、登记和更新各平台 skill，并在用户明确要求时向当前 Agent 提供结构化 skill 推荐上下文。

核心隐喻：

```text
Agent 是大脑，负责理解、推理和执行。
SkillCere 是小脑，负责整理 skill 清单、版本和安装状态，让 Agent 更顺滑地决定该用哪些 skill。
```

## 当前阶段

这是 SkillCere 的公开发布版本，当前重点是中央索引和任务前推荐上下文。公开仓库不包含作者本机的 skill 索引、安装日志、本地扫描路径或导出文件；首次运行时会在用户自己的环境中生成这些数据。

第一版目标：

```text
扫描现有 skill
建立中央索引
发现新安装 skill 并登记
按需提供推荐所需的 skill 上下文
由当前 Agent 基于上下文推荐 skill
由当前 Agent 生成启动说明，但默认不直接执行任务
默认使用 Git 同步中央索引
```

第一版暂不做：

```text
不强制共享 skill 文件本体
不默认复制 skill 到所有平台
不做复杂补丁机制
不自动删除任何工具目录里的 skill
不把缓存、临时目录、node_modules 当成正式 skill 来源
```

## 目录结构

```text
SkillCere/
├── SKILL.md                  # SkillCere skill 入口
├── scripts/
│   └── skillcere.py          # skill 辅助脚本和 CLI
├── skill-index.json          # 中央 skill 索引
├── platforms.json            # 平台标识配置，不含本机真实路径
├── platforms.local.example.json # 本机扫描路径示例
├── platforms.local.json      # 本机扫描路径，默认不提交
├── install-log.jsonl         # 发现、安装、更新记录
├── version-cache.json        # 远程版本检查缓存
├── exports/                  # 本地 Excel 导出，默认不提交
└── docs/                     # 设计文档和后续说明
```

`platforms.local.json` 用于手动配置和修改本机扫描地址。它包含本机路径，已加入 `.gitignore`，不应上传到 GitHub。

`exports/` 是本地查看用输出目录，也已加入 `.gitignore`。

公开仓库中的 `skill-index.json`、`install-log.jsonl` 和 `version-cache.json` 是空白起始文件。运行 `scan` 后，它们会反映你自己的本机 skill 环境。

## 计划命令

```powershell
python .\scripts\skillcere.py scan
python .\scripts\skillcere.py status
python .\scripts\skillcere.py context "用户需求"
python .\scripts\skillcere.py sync
```

后续再扩展：

```powershell
skillcere check-updates
```

## 当前可用命令

扫描本机已安装 skill：

```powershell
python .\scripts\skillcere.py scan
```

`scan` 默认会在扫描后执行 `sync`，只提交/推送中央清单相关文件：

```text
skill-index.json
install-log.jsonl
version-cache.json
platforms.json
```

它不会同步 `platforms.local.json`、`exports/`、用户任务文本或代码改动。

如果只想本地扫描、不触发 Git 同步：

```powershell
python .\scripts\skillcere.py scan --no-sync
```

查看中央索引状态：

```powershell
python .\scripts\skillcere.py status
```

生成给 Agent 使用的 skill 推荐上下文：

```powershell
python .\scripts\skillcere.py context "帮我做一个高质量前端页面，并用浏览器截图验证效果"
```

`context` 不调用任何模型 API，也不需要 API key。它只输出 skill 清单上下文和推荐指令，由当前 Agent 使用自己的模型能力完成最终推荐。

`recommend` 暂时保留为 `context` 的别名。

同步中央 skill 清单：

```powershell
python .\scripts\skillcere.py sync
```

预览将同步哪些清单文件：

```powershell
python .\scripts\skillcere.py sync --dry-run
```

只提交到本地 Git、不推送远程：

```powershell
python .\scripts\skillcere.py sync --no-push
```

如果仓库没有配置 GitHub remote，`sync` 会提交到本地 Git，并提示远程未配置。

## Skill 形态

SkillCere 的推荐不由 CLI 直接完成，而是通过仓库根目录的 `SKILL.md` 作为统一 `skillcere` skill 接入到各 Agent。

## 直接作为 Skill 包使用

把整个 `SkillCere` 目录放进目标 Agent 的 skill 目录即可，例如：

```text
<agent-skill-dir>/skillcere/
├── SKILL.md
├── scripts/
│   └── skillcere.py
└── ...
```

首次运行时，如果缺少本地项目文件，SkillCere 会自动创建：

```text
skill-index.json
platforms.json
platforms.local.json
install-log.jsonl
version-cache.json
```

其中 `platforms.local.json` 是用户自己的扫描路径配置，可以手动修改。默认会尝试扫描：

```text
~/.codex/skills
~/.agents/skills
~/.claude/skills
~/.gemini/skills
```

如果这个 skill 包不是一个 Git 仓库，`scan` 默认触发的 `sync` 会自动跳过 Git 同步；扫描和推荐上下文功能仍然可用。需要 GitHub 同步时，应通过 `git clone` 安装，或在该目录初始化 Git 并配置 remote。

它有两种使用方式：

```text
显式推荐介入：
用户要求 SkillCere 或询问哪些 skill 可以辅助任务
→ skillcere 先 scan，并默认 sync 中央清单
→ skillcere 再生成 context
→ 当前 Agent 基于 context 推荐 skill
→ 当前 Agent 生成启动说明
→ 默认停止，不直接执行任务

手动总控：
用户显式要求 skillcere 扫描、查看状态、导出 Excel、清理失联 skill
→ skillcere 直接调用对应本地命令
```

当前 skill 入口位置：

[SKILL.md](./SKILL.md)

## 推荐流程

```text
用户明确要求 skill 推荐
  ↓
调用 skillcere context
  ↓
SkillCere 读取中央索引和本机安装状态
  ↓
输出 skill 清单上下文
  ↓
当前 Agent 基于上下文推荐 skill 并生成启动说明
  ↓
默认停止，等待用户确认是否继续执行
```

SkillCere 的任务上下文只做即时输出，不保存用户需求或任务原文。

## 命名约定

```text
正式名称：SkillCere
中文名称：技能小脑
命令名称：skillcere
```

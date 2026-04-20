# SkillCere

SkillCere（技能小脑）是一个跨 Agent 的 skill 清单管理与推荐上下文系统，用于持续发现、登记和更新各平台 skill，并在任务开始前向当前 Agent 提供结构化 skill 上下文。

核心隐喻：

```text
Agent 是大脑，负责理解、推理和执行。
SkillCere 是小脑，负责整理 skill 清单、版本和安装状态，让 Agent 更顺滑地决定该用哪些 skill。
```

## 当前阶段

这是 SkillCere 的第一版仓库骨架，当前重点是中央索引和任务前推荐上下文。

第一版目标：

```text
扫描现有 skill
建立中央索引
发现新安装 skill 并登记
提供推荐所需的 skill 上下文
由当前 Agent 基于上下文推荐 skill
由当前 Agent 生成启动说明
使用 Git 备份中央索引
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
├── skill-index.json          # 中央 skill 索引
├── platforms.json            # 平台标识配置，不含本机真实路径
├── platforms.local.json      # 本机扫描路径，默认不提交
├── install-log.jsonl         # 发现、安装、更新记录
├── version-cache.json        # 远程版本检查缓存
├── bridge-skills/            # 各 Agent 的接入 skill 模板
└── docs/                     # 设计文档和后续说明
```

`platforms.local.json` 用于手动配置和修改本机扫描地址。它包含本机路径，已加入 `.gitignore`，不应上传到 GitHub。

## 计划命令

```powershell
python .\skillcere.py scan
python .\skillcere.py status
python .\skillcere.py context "用户需求"
```

后续再扩展：

```powershell
skillcere check-updates
skillcere sync
```

## 当前可用命令

扫描本机已安装 skill：

```powershell
python .\skillcere.py scan
```

查看中央索引状态：

```powershell
python .\skillcere.py status
```

生成给 Agent 使用的 skill 推荐上下文：

```powershell
python .\skillcere.py context "帮我做一个高质量前端页面，并用浏览器截图验证效果"
```

`context` 不调用任何模型 API，也不需要 API key。它只输出 skill 清单上下文和推荐指令，由当前 Agent 使用自己的模型能力完成最终推荐。

`recommend` 暂时保留为 `context` 的别名。

## 推荐流程

```text
用户提出任务
  ↓
调用 skillcere context
  ↓
SkillCere 读取中央索引和本机安装状态
  ↓
输出 skill 清单上下文
  ↓
当前 Agent 基于上下文推荐 skill 并生成启动说明
```

SkillCere 的任务上下文只做即时输出，不保存用户需求或任务原文。

## 命名约定

```text
正式名称：SkillCere
中文名称：技能小脑
命令名称：skillcere
```

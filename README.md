# SkillCere

SkillCere（技能小脑）是一个跨 Agent 的技能协调系统，用于持续发现、登记和更新各平台 skill，并在任务开始前根据需求推荐可用的 skill、版本状态和启动说明。

核心隐喻：

```text
Agent 是大脑，负责理解、推理和执行。
SkillCere 是小脑，负责协调 skill、版本和任务启动动作，让执行更顺滑。
```

## 当前阶段

这是 SkillCere 的第一版仓库骨架，当前重点是中央索引和任务前推荐能力。

第一版目标：

```text
扫描现有 skill
建立中央索引
发现新安装 skill 并登记
检查推荐 skill 的版本
根据任务推荐可用 skill，并给出必要的平台提示
生成 Agent 启动说明
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
skillcere init
skillcere scan
skillcere recommend "用户需求"
skillcere check-updates
skillcere sync
skillcere status
```

## 推荐流程

```text
用户提出任务
  ↓
调用 skillcere recommend
  ↓
SkillCere 读取中央索引和本机安装状态
  ↓
根据需求推荐 skill
  ↓
检查安装状态和版本状态
  ↓
输出可直接交给执行 Agent 的启动说明
```

SkillCere 的任务推荐只做即时输出，不保存用户需求或任务原文。

## 命名约定

```text
正式名称：SkillCere
中文名称：技能小脑
命令名称：skillcere
```

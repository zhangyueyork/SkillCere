---
name: skillcere
description: "SkillCere control skill for skill recommendation and skill inventory management. Use only when the user explicitly asks to use SkillCere, asks which skills can help with a task, asks for skill recommendations before work, or requests skill management actions such as scan, sync, status, export, or prune. Do not use automatically for ordinary user tasks that do not ask for skill recommendation or SkillCere."
---

# SkillCere

Use this skill as the unified entrypoint for SkillCere.

Recommendation role:

- When the user asks for skill recommendation or explicitly invokes SkillCere, call SkillCere.
- Refresh and sync the local skill index when needed.
- Gather the currently available skills and their install status.
- Check whether version status is known or unknown.
- Produce a structured context so the current Agent can decide which skills to use.
- Generate a startup instruction for a future executing Agent.
- Stop after recommendation unless the user explicitly asks to continue with execution.

Manual role:

- Run skill inventory scans.
- Sync central skill list files through Git.
- Show current index status.
- Export the skill list to Excel.
- Prune skills that are no longer installed.

## Core Principle

SkillCere Core manages the skill registry.

The current Agent performs the actual recommendation.

That means:

- SkillCere Core does not call an external model API.
- SkillCere Core only returns registry facts and recommendation context.
- The current Agent reads that context and decides which skills to recommend.

## Recommendation Workflow

Use this workflow only when the user asks to use SkillCere, asks what skills can help, or asks for skill recommendations before starting work.

First resolve `<skillcere-root>` as the directory that contains this `SKILL.md`.

Then:

1. Restate the user's task in one concise sentence.
2. Refresh the local index:

```powershell
python "<skillcere-root>\scripts\skillcere.py" scan
```

`scan` syncs the central index by default. Use `scan --no-sync` only for local tests or when the user explicitly asks not to sync.

3. Generate SkillCere context:

```powershell
python "<skillcere-root>\scripts\skillcere.py" context "<user task>"
```

4. Read the returned context carefully.
5. As the current Agent, decide:
   - which skills are most relevant,
   - which of them are already installed,
   - whether installation or update may be needed,
   - what startup instruction should be given before execution.
6. Present the result in this shape:
   - recommended skills,
   - version status,
   - install/update suggestion,
   - startup instruction for the executing Agent.
7. Stop after presenting the recommendation. Do not execute the user's underlying task unless the user explicitly says to continue or start.

## Manual Management Actions

Use these when the user explicitly asks to manage SkillCere.

### Scan skills

```powershell
python "<skillcere-root>\scripts\skillcere.py" scan
```

### Scan without sync

```powershell
python "<skillcere-root>\scripts\skillcere.py" scan --no-sync
```

### Sync central skill index

```powershell
python "<skillcere-root>\scripts\skillcere.py" sync
```

### Preview syncable changes

```powershell
python "<skillcere-root>\scripts\skillcere.py" sync --dry-run
```

### Show status

```powershell
python "<skillcere-root>\scripts\skillcere.py" status
```

### Export Excel

```powershell
python "<skillcere-root>\scripts\skillcere.py" export-excel --current-only
```

### Preview prune candidates

```powershell
python "<skillcere-root>\scripts\skillcere.py" prune
```

### Delete not-installed skills from the index

```powershell
python "<skillcere-root>\scripts\skillcere.py" prune --drop-not-installed
```

## Output Contract For Task-Start Use

After reading SkillCere context, produce:

### 1. Recommended skills

- Skill id
- Why it is relevant
- Which task step it helps with

### 2. Version status

- Known version or unknown
- Whether remote latest version can be confirmed

### 3. Install or update suggestions

- Already installed in current platform
- Installed in another platform
- Missing and may need installation

### 4. Startup instruction

A concise instruction the executing Agent can directly follow, for example:

```text
Please use frontend-design and agent-browser for this task.
First use frontend-design to plan and implement the page.
Then use agent-browser to validate the result with browser screenshots.
If a required skill is not installed in the current platform, install it first or switch to a platform where it is already available.
```

## Constraints

- Do not use SkillCere automatically for ordinary tasks that do not ask for skill recommendation.
- Do not execute the underlying user task after recommending skills unless the user explicitly asks to continue.
- Do not save user task text into SkillCere.
- Do not modify tool skill directories unless the user explicitly asks.
- Do not treat cache, temp, vendor, or `node_modules` directories as official skill sources.
- Do not invent source URLs or versions that SkillCere does not know.
- Treat platform hints as secondary. The primary output is the recommended skill set.
- Only sync central registry files. Do not sync `platforms.local.json`, Excel exports, user tasks, or unrelated code changes.

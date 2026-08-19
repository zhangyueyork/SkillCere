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
- Discover enabled/installed Codex plugin skills without executing plugin code.
- Search the reviewed candidate registry when installed skills do not cover the task.
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

The scan reads standalone skill roots plus Codex plugin configuration, remote-install markers, plugin manifests, and plugin `SKILL.md` files. Plugin skills use `plugin-name:skill-name` ids. A plugin record means the plugin is installed/configured; it does not guarantee that Codex included that skill in a particular turn's size-limited initial skill list.

3. Generate SkillCere context:

```powershell
python "<skillcere-root>\scripts\skillcere.py" context "<user task>"
```

The context contains two separate catalogs:

- installed/indexed skills from `skill-index.json`;
- reviewed but not installed candidates from `candidate-index.json`.

Candidate records are metadata only. They do not mean that third-party skill files or scripts are installed, trusted, or ready to execute.

4. Read the returned context carefully.
5. Use external skill discovery when useful:
   - If the indexed/installed skill list is incomplete for the task, invoke the available `find-skills` capability or CLI to search external skills.
   - Keep external search results separate from indexed/installed skills.
   - Do not present external skills as installed unless SkillCere context explicitly shows them in `installed_on`.
6. As the current Agent, decide:
   - which skills are most relevant,
   - which of them are already installed,
   - which external candidate skills may be worth installing,
   - whether installation or update may be needed,
   - what startup instruction should be given before execution.
7. Present the result in this shape:
   - recommended skills,
   - external candidate skills, when any were found,
   - version status,
   - install/update suggestion,
   - startup instruction for the executing Agent.
8. Stop after presenting the recommendation. Do not execute the user's underlying task unless the user explicitly says to continue or start.

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

Use `scan --no-plugins` only to diagnose standalone skill roots without reading the Codex plugin inventory.

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

### List candidate skills

```powershell
python "<skillcere-root>\scripts\skillcere.py" candidates
python "<skillcere-root>\scripts\skillcere.py" candidates --query "obsidian"
python "<skillcere-root>\scripts\skillcere.py" candidates --status shortlisted
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
- Exact installed platforms from `installed_on`; if none are listed, say the index has no recorded installed platform

### 2. External candidate skills

- Skill id/name from `candidate-index.json` or `find-skills`
- Why it may help
- Candidate status and pinned source when present in `candidate-index.json`
- Install command or source only when provided by the registry or `find-skills`
- Clear note that a candidate is not installed

Omit this section only when external discovery was not needed or found no useful candidates.

### 3. Version status

- Known version or unknown
- Whether remote latest version can be confirmed

### 4. Install or update suggestions

- Already installed in current platform
- Installed in another platform
- Missing and may need installation
- External candidate skills that need installation before use

### 5. Startup instruction

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
- Read Codex plugin cache only through validated `.codex-plugin/plugin.json` manifests for plugins that config or remote-install metadata identifies as installed; never execute or modify cached plugin code.
- Do not invent source URLs or versions that SkillCere does not know.
- Do not invent external skill names, source URLs, install commands, or versions that were not returned by `find-skills`.
- Do not present a `candidate-index.json` record as installed. Recheck its pinned source, license, dependencies, scripts, and platform compatibility before recommending installation.
- Always report exact installed platforms for recommended indexed skills using the `installed_on` field.
- Treat platform hints as secondary. The primary output is the recommended skill set.
- Only sync central registry files. Do not sync `platforms.local.json`, Excel exports, user tasks, or unrelated code changes.

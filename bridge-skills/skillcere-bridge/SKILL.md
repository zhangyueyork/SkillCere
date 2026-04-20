---
name: skillcere-bridge
description: "Task-start bridge for SkillCere. Use before starting a new task when skill selection or version checks may matter."
---

# SkillCere Bridge

Use this skill at the beginning of a new task when the task may benefit from skill recommendation or version checks.

## Purpose

SkillCere Bridge connects the current Agent to SkillCere, the user's cross-Agent skill coordination system.

SkillCere Core should provide context for the current Agent to decide:

- Which skills exist in the central index.
- Where relevant skills are already installed.
- Whether those skills have known versions or source URLs.
- What constraints the Agent should observe when recommending skills.

## Workflow

1. Restate the user's task in one concise sentence.
2. Call the local SkillCere command when available:

```powershell
skillcere context "<user task>"
```

3. Read the returned SkillCere context.
4. As the current Agent, use your own reasoning to recommend the most relevant skills from that context.
5. If recommended skills are not available in the current platform, tell the user where they are installed or whether they need installation.
6. Generate startup instructions for the executing Agent.
7. If `skillcere` is not installed yet, explain that SkillCere Core is not available and proceed with the best local skill choice.

## Expected Output From This Bridge

After reading SkillCere context, this bridge should produce:

- Recommendation rationale.
- Recommended skills.
- Version check results.
- Install or update plan.
- Startup instructions for the executing Agent.

## Constraints

- Do not modify tool skill directories directly.
- Do not install or update skills unless the user explicitly asks or the current Agent has a safe install workflow.
- Do not treat cache, temp, vendor, or `node_modules` directories as official skill sources.
- Treat platform hints as secondary. The primary output is the recommended skill set.
- Do not ask SkillCere Core to call an external model API. The current Agent performs the recommendation.

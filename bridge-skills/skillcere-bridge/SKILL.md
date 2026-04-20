---
name: skillcere-bridge
description: "Task-start bridge for SkillCere. Use before starting a new task when platform or skill selection may matter."
---

# SkillCere Bridge

Use this skill at the beginning of a new task when the task may benefit from platform selection, skill recommendation, or version checks.

## Purpose

SkillCere Bridge connects the current Agent to SkillCere, the user's cross-Agent skill coordination system.

SkillCere should decide:

- Which platform is most suitable for the task.
- Which skills should be used.
- Whether required skills are installed on the recommended platform.
- Whether those skills need updates.
- What startup instructions should be given to the executing Agent.

## Workflow

1. Restate the user's task in one concise sentence.
2. Call the local SkillCere command when available:

```powershell
skillcere recommend "<user task>"
```

3. Read the returned recommendation.
4. If the current platform is not the recommended platform, tell the user which platform SkillCere recommends and why.
5. If the current platform is suitable, continue using the returned startup instructions.
6. If `skillcere` is not installed yet, explain that SkillCere Core is not available and proceed with the best local skill choice.

## Expected Output From SkillCere

SkillCere recommendations should include:

- Recommended execution platform.
- Recommendation rationale.
- Recommended skills.
- Version check results.
- Install or update plan.
- Startup instructions for the executing Agent.

## Constraints

- Do not modify tool skill directories directly.
- Do not install or update skills unless the user explicitly asks or the current Agent has a safe install workflow.
- Do not treat cache, temp, vendor, or `node_modules` directories as official skill sources.
- Prefer the recommended platform based on task fit, not only on already installed skills.


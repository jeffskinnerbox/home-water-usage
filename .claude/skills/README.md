<!--
Maintainer:   jeffskinnerbox@yahoo.com / www.jeffskinnerbox.me
Version:      0.0.0
-->

<div align="center">
<img src="https://raw.githubusercontent.com/jeffskinnerbox/blog/main/content/images/banners-bkgrds/work-in-progress.jpg"
        title="These materials require additional work and are not ready for general use." align="center" width=420px height=219px>
</div>

---------------

```bash
# within your project directory, make your skills directory
mkdir -p <project-directory>/.claude/skills

# copy the desired skill to your project
cp -r ~/src/projects/makersmiths/skills/<skill-category>/<target-skill>  <project-directory>/.claude/skills
```





# Purpose of This Skills Folder
[Agent Skills][08] are folders of instructions, scripts, and resources that agents can discover and use to do things more accurately and efficiently.

Released in October 2025, skills represent a fundamental shift in how [Anthropic's Claude Code][02] can customize AI assistants.
Skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks.
Skills teach Claude how to complete specific tasks in a repeatable way,
whether that's creating documents with your company's brand guidelines,
analyzing data using your organization's specific workflows,
or automating personal tasks.

This short document is intended to help you maintain and enhance these skill documents for your needs.
Its we worth reading online documentation and videos to understand Claude Code.
This `README.md` is intended to give you key information so you can customize or expand these skills.

## Some Quick Claude Code Training
I have found the Claude Pro plan, costing $20/mo., very much worth the investment.

* [Claude Skills Explained in 23 Minutes](https://www.youtube.com/watch?v=vEvytl7wrGM)
* [Claude Code Clearly Explained (and how to use it)](https://www.youtube.com/watch?v=zxMjOqM7DFs)
* [How to Set Up Claude Code in 2026 (Beginner Tutorial)](https://www.youtube.com/watch?v=kddjxKEeCuM)
* [Claude Code Tutorial](https://www.youtube.com/playlist?list=PL4cUxeGkcC9g4YJeBqChhFJwKQ9TRiivY)

* [Confessions of an Ex-Coder](https://the-gigi.github.io/gigi-zone/posts/2025/11/confesstions_of_an_ex_coder/)
* [Claude Code Deep Dive — Basics](https://the-gigi.github.io/gigi-zone/posts/2026/01/cc-deep-dive-01-basics/)
* [Claude Code Deep Dive — Slash Commands](https://the-gigi.github.io/gigi-zone/posts/2026/01/cc-deep-dive-02-slash-commands/)
* [Claude Code Deep Dive — Total Recall](https://the-gigi.github.io/gigi-zone/posts/2026/01/cc-deep-dive-03-total-recall/)
* [Claude Code Deep Dive — Mad Skillz](https://the-gigi.github.io/gigi-zone/posts/2026/01/cc-deep-dive-04-mad-skillz/)
* [Claude Code Deep Dive — MCP Unleashed](https://the-gigi.github.io/gigi-zone/posts/2026/01/cc-deep-dive-05-mcp-unleashed/)

## How Skill Activation Works
When you make a request, Claude Code follows a [progressive disclosure pattern for writing agentic skills][05].
It only loads what it needs, when it needs it.
This keeps interactions fast while giving you access to powerful capabilities on demand.
The skill activation flowchart has three phases:

* Discovery - scan directories, load metadata
* Matching - check if request matches skill
* Execution - load `SKILL.md`, follow instructions, complete task

The key insight: Claude scans skill directories and reads only the metadata (name + description) until it finds a match.
Only then does it load the full instructions.
This means you can have dozens of skills installed without slowing down normal interactions.

## SKILL.md Structure
Think of a `SKILL.md` like a recipe card for Claude — it tells the model when to activate, what to do, and how to do it.

Key Design Principles
* **Keep `SKILL.md` under ~500 lines.** If it's longer, use `references/` subdirectory with clear pointers — think of it like progressive disclosure (metadata → SKILL.md body → reference files).
* **Explain *why*, not just *what*.** Instead of "MUST do X," explain the reasoning so Claude generalizes correctly.
* **Include examples** with input/output pairs where possible.
* **No human on-boarding docs** (no README, CHANGELOG, etc.) — the audience is Claude, not a developer.

### SKILL.md Directory Structure
The only required file is `SKILL.md`.
Everything else — `scripts`, `references`, `assets` — is optional alongside it.

The `SKILL.md` is the entry point that Claude reads first.
Supporting scripts and files load only when explicitly needed.

A skill at `.claude/skills/deploy/SKILL.md` and a command at `.claude/commands/deploy.md` are equivalent,
but if they share a name, the skill takes precedence.

```text
.claude/skills/              # or ~/.claude/skills/ for global
└── your-skill-name/
    ├── SKILL.md             # required — entry point, frontmatter + instructions
    ├── scripts/             # optional shell/python helpers
    │   └── helper.sh
    ├── references/          # optional supporting context/data files
    │   └── common-cases.md
    └── assets/              # templates, icons, fonts used in output
```

### SKILL.md File Template
Claude scans each skill's `name` and `description` from YAML frontmatter using ~100 tokens per skill.
The full instructions only load when the skill is deemed relevant,
so keep the frontmatter description tight and trigger-specific — it's essentially the skill's activation condition.

`CLAUDE.md` is for always-on project context but skills are for triggered workflows.
Loading every workflow into `CLAUDE.md` bloats the main context, so don't do it.

The `SKILL.md` is the entry point — think of it as working memory for that task.
Keep process steps here; put bulky reference data in separate files in the `referances` directory.

```markdown
---
name: your-skill-name
description: "One or two sentences Claude uses to decide when to activate this skill. Be specific about trigger conditions —
              e.g. 'Use when the user asks to run tests, create a PR, or check CI status.'"
---

# Skill Title
The `description` is the **primary trigger mechanism** — it's always in context (~100 words) and determines when the skill fires.
Include both what the skill does AND specific user phrases/contexts that should activate it.

## Overview
A brief paragraph explaining the skill's purpose and high-level approach. Like a docstring for the whole skill.

## When to Use
A table or short section mapping common tasks to approaches — lets Claude quickly orient without reading the whole file.
- Trigger condition 1
- Trigger condition 2
- Trigger condition 3

## Core Instructions Steps / Workflow
The meat. Step-by-step procedures, code patterns, critical rules. Written in imperative form.
This is where you put: How to accomplish the task, Code snippets and templates, Decision trees (if task A → do X, if task B → do Y).

1. First action Claude should take
2. Second action
3. Third action — be explicit, Claude follows sequences more reliably than prose

## Output Format
Describe the expected output structure, e.g.:

- Summary paragraph
- A table of results
- A code block with X format

## Critical Rules / Pitfalls / Constraints
Explicit do's and don'ts. Things like "NEVER use unicode bullets" or "ALWAYS validate after creating."
These are guardrails from hard-won debugging.

* Do not modify X — only report issues
* Always ask before Y
* Never Z
```

---------------

## Where to Put Your Skills

| Location | Scope | When to Use |
|:------------:|:------------:|:------------:|
| `~/.claude/skills/` | Global - Available to you personal but for all projects | General purpose skills like code review, documentation |
| `.claude/skills/` | Local - Only available to this project, in git repo | Project specific workflows like team conventions |


>**NOTE:** commands (`/.claude/commands/`) have been merged into the skills system.
>A skill and a command with the same name are equivalent, but skills take precedence.

Check to see what you might already have globally:

```bash
# check what claude skills you have already installed or acquired
ls ~/.claude/skills/
code-doc-writer/  code-reviewer/  project-doc-writer/  skill-generator/  test-generator/
```

---------------

## Where Can I Acquire Existing `SKILL.md` Files?
* Anthropics public repository for Agent Skills - [GitHub: anthropics/skills](https://github.com/anthropics/skills/)

## Native Claude Skills
Already existing global skills found in `~/.claude/skills`
* `code-doc-writer`
* `code-reviewer`
* `project-doc-writer`
* `skill-generator`
* `test-generator`

## Makersmiths Skills
* `bill-of-materials-generator` — generates itemized BOM with per-student costs, optional items, shared supplies,
  shipping, and cost summaries. Single source of truth for all cost and sourcing information.
* `lesson-plan-generator` — generates session-level teaching guides for volunteer makerspace instructors.
  Adapted from "[How to Build Claude Skills: Lesson Plan Generator Tutorial][01]"
* `syllabus-generator` — generates course-level syllabi with schedule, objectives, and structure.
  Adapted from "[Syllabus Templates - Center for Teaching Excellence][03]"
* `explainer` — adapted from  "[Claude Skills Explained in 23 Minutes][06]" and "[GitHub: ShawhinT/ai-tutor-skill][07]"

TBD
* `project-memory` — adapted from "[Build Your First Claude Code Agent Skill: A Simple Project Memory System That Saves Hours][04]"

These three course-document skills are designed to work together:

| Skill | Produces | Contains |
|:------|:---------|:-----|
| `syllabus-generator` | Course syllabus | Topics, schedule, objectives, structure, assessment |
| `lesson-plan-generator` | Per-session lesson plans | Teaching instructions, timing, troubleshooting |
| `bill-of-materials-generator` | Bill of materials | All costs, quantities, sourcing, shipping |

**Key Rule:** Cost / pricing and sourcing information belongs exclusively in the BOM.
The syllabus and lesson plans reference component names, and links if possible, but never include purchase links.


## Some Definitions
workflow
Prompts
MCP
Plugins
AI agent

## Agent Skill Structure Anatomy
A agent skill is simply a folder containing a `SKILL.md` file
and optional supporting resources.
The `SKILL.md` file has two parts:

* **YAML frontmatter:** Metadata that tells Claude when to activate the skill
* **Markdown body:** Instructions Claude follows when the skill is active

Think of skills as reusable “expert modes” you can install.
When you say “set up project memory,” Claude doesn’t just guess what you mean.
It loads specifically the `SKILL.md` file in `project-memory/`



## What are Claude Skills?
Claude Skills are organized folders having instructions, scripts, and resources that Claude can discover
and load to perform the specified tasks.
They help encode repeatable workflows into Claude AI,
transforming it from a general-purpose assistant into a specialized agent that is tailored to your needs.

Building a skill is like putting together an on-boarding guide for a new employee (aka AI agent).
Instead of repeatedly explaining the same process or writing lengthy prompts every time you need something done,
you package your expertise once, and Claude applies it automatically whenever relevant.

## What Exactly is a Skill?
A skill is a directory containing a `SKILL.md` file along with folders of instructions, scripts,
and resources that give agents additional capabilities.
The `SKILL.md` file includes metadata (name, description, and optional dependencies) written in YAML,
along with detailed instructions written in plain Markdown.
When we assign a task, Claude checks which skills match,
and only relevant skills get loaded along with the necessary parts.
This means we can maintain dozens of skills without overwhelming Claude’s context window.

### Agent vs. SubAgent
In Claude Code, the agent is the main AI session, acting as the primary orchestrator,
while subagents are specialized, independent agents spawned to handle specific tasks in separate, isolated context windows.
Subagents prevent context pollution by managing detailed work (like testing or debugging) separately,
reporting only the final results back to the main agent.

### Skills vs. Prompts
Traditional prompts are one-time instructions you repeat in each conversation.
Every time you need Claude to perform a task,
you must remember or copy and paste complex instructions.
Skills bundle the exact ingredients a task needs, clear instructions, optional templates, and code so they can be tested and versioned

### Skills vs. MCP
MCP connects Claude to external systems such as databases, APIs, tools.
MCP solves tool orchestration.
Skills teach Claude how to perform tasks with procedures, workflows, and standards.
Skills solve workflow orchestration.

### Skills vs. Plugins
Unlike traditional plugins that require complex APIs, authentication setups, and server infrastructure,
skills are just files and folders that’re easy to version control and distribute.
This makes skills far more accessible. If you can write documentation, you can create a skill.

## How to Build the SKILL.md File in Claude?
Think of `SKILL.md` file as a instruction manual that lets Claude understand your workflow.
The subsections below are the key components to add to the `SKILL.md` file.

### Metadata
Metadata tells Claude the basic details about the skill before it even reads the main content.
It helps organize and categorize the skill so that Claude and users know its purpose, author, and other attributes.
The metadata is written at the top of the file inside a YAML block (`---`),
and it must follow proper indentation and formatting

* Required fields:
  * `name`: A concise, descriptive name for the skill.
  * `description`: A short explanation of what the skill does and when to use it.
* Optional fields:
  * `version`: Tracks updates or iterations of your skill.
  * `license`: Specifies usage rights if shared publicly.
  * `metadata`: A flexible field to include author name, tags, or project references.

### Instruction Body
The body of the file written below the YAML block defines how Claude should perform the skill.
This is the actual playbook Claude follows step by step.
The instruction body should be easy to scan, with clear sections and direct language.
Claude relies on structure and clarity, so formatting and phrasing impact how well it executes the skill.

A good instruction body typically includes
(Using these titles is useful but not required):

* `What This Skill Does`: A quick summary of what the skill does.
* `Prerequisites`: What software should be installed and what knowledge needed (e.g. basic understanding of teaching and learning practices)
* `When to Use`: What will trigger the use of this skill
* `Core Capabilities` / `Inputs and Outputs`: Specify what data the skill expects (like a topic or file) and what it should produce (like a formatted lesson plan).
* `Example Workflow` / `Execution Steps`: A numbered or bulleted list outlining the process Claude must follow.
* `Examples`: Optional examples showing input-output pairs to clarify expectations.
* `Success Criteria`:

>**Note:** YAML is sensitive to indentation and formatting.
>Use consistent spacing (usually two spaces, not tabs),
>avoid special characters in field names, and ensure the format is
>wrapped between triple dashes (`---`) at the beginning and end.

## How to Build Skills Directory Structure?
Before writing the skill, it’s essential to set up the folder structure.
Claude expects skills to be organized in a way that it can locate files and execute instructions properly.

The project skills folder should look like this:

```text
.claude/
├── commands/            # Custom slash commands (/my-command)
├── skills/              # Auto-invoked task guides (your SKILL.md files go here)
│   └── my-skill/
│       ├── SKILL.md
│       └── scripts/
├── agents/              # Specialized subagents for domain-specific tasks
├── hooks/               # Event-driven automation (run linting, tests, etc.)
├── rules/               # Path-specific rules (e.g., frontend.md, backend.md)
├── settings.json        # Shared team permissions, tool rules, MCP config
├── settings.local.json  # Personal overrides (gitignore this)
└── .mcp.json            # MCP server integrations
```

Here's what each one actually does:

* `commands/` — Markdown files that become /slash-commands you can invoke manually. Great for frequent operations like running a full test suite, generating a PR description, or deploying to staging.
* `skills/` — This is where your SKILL.md files live. Skills are automatically called by Claude when it determines they are necessary M, unlike commands which you invoke explicitly. Each skill lives in its own subfolder with a SKILL.md and optional scripts.
* `agents/` — Subagent configurations for specialized tasks GitHub like code review, security auditing, or architecture decisions. Each runs in its own context window.
* `hooks/` — Event-driven automation triggered by events like PostToolUse, PreCommit, PostCommit, OnFileChange M. Common use: auto-run lint:fix after every file edit.
* `rules/` — Path-scoped instruction files. You can have frontend.md, backend.md, testing.md etc. that only apply when Claude is working in those parts of the codebase.
* `settings.json` — Configure permissions, environment variables, and tool behavior Claude. This is the shared team version — commit it to git.
* `settings.local.json` — Your personal overrides. Add this to .gitignore.
* `.mcp.json` — MCP server definitions for extending Claude with external tools (GitHub, Postgres, Slack, etc.).

The general rule of thumb: commit `commands/`, `skills/`, `agents/`, `settings.json`, and `rules/` since they benefit the whole team. Keep `settings.local.json` gitignored for personal preferences.




* `SKILL.md`: The core file that defines metadata, logic, and instructions for Claude.
* `scripts/`: Executable code for deterministic tasks
* `references/`: Docs loaded into context as needed. Contains content blueprints for different parts of the lesson plan such as outlines, quizzes, and exercises.
* `assets/`: Stores templates, icons, fonts used in output. Sample outputs or reference materials that help Claude understand the expected format.
>**NOTE:** This directory structure was generated via this Linux command: `tree -F --filesfirst skills`.


---------------

## Claude Quick Start Guide
* [Claude Code Course — Step-by-Step Guide from CLI to Real Workflows](https://www.youtube.com/playlist?list=PL-F5kYFVRcIvZQ_LEbdLIZrohgbf-Vock)
* [Claude Code Tutorial](https://www.youtube.com/playlist?list=PL4cUxeGkcC9g4YJeBqChhFJwKQ9TRiivY)
* [Mastering Claude Skills: The Complete Guide to Building Effective Agent Skills](https://skillzwave.ai/ai-agent-guides/mastering-claude-skills-the-complete-guide-to-building-effective-agent-skills/)

### Installing Claude Code
Work with Claude directly in your codebase. Build, debug, and ship from your terminal, IDE, Slack, or the web.
Describe what you need, and Claude handles the rest.

Work with Claude directly in your terminal.
Claude explores your codebase context, answers questions, and make changes.
It can even use all your CLI tools.

```bash
# install claude code on your  computer
curl -fsSL https://claude.ai/install.sh | bash
```

* [The Definitive Guide to Claude Code: From First Install to Production Workflows](https://blog.devgenius.io/the-definitive-guide-to-claude-code-from-first-install-to-production-workflows-6d37a6d33e40)
* [The Advanced Claude Code Setup Guide](https://blog.devgenius.io/the-advanced-claude-code-setup-guide-358f7b69334d)
* [Everything Claude Code: The Repo That Won Anthropic Hackathon (Here’s a Breakdown)](https://medium.com/@joe.njenga/everything-claude-code-the-repo-that-won-anthropic-hackathon-33b040ba62f3)
* [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)
* [10 GitHub Repositories To Master Claude Code](https://www.kdnuggets.com/10-github-repositories-to-master-claude-code)

### Install Claude Skills
* [Claude Skills in 13 Minutes (Full Walkthrough)](https://www.youtube.com/watch?v=NH74es_MBjE)
* [Claude Skills Explained in 23 Minutes](https://www.youtube.com/watch?v=vEvytl7wrGM)

### Install Claude-Mem Plugin
`Claude-Mem` is a Claude Code plugin that automatically captures everything Claude does during your coding sessions,
compresses it with AI (using Claude's `agent-sdk`), and injects relevant context back into future sessions.

Claude-Mem seamlessly preserves context across sessions by automatically capturing tool usage observations,
generating semantic summaries, and making them available to future sessions.
This enables Claude to maintain continuity of knowledge about projects even after sessions end or reconnect.

```claude
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

* [Give Claude Persistent Memory in 5 Minutes](https://www.youtube.com/watch?v=ryqpGVWRQxA)
* [Claude Code With UNLIMITED Memory! Solves Claude's Memory Problem!](https://www.youtube.com/watch?v=qhuS__jC4n8)
* [Claude-Mem](https://claude-mem.ai/)
* [GitHub: thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)

### Install LSP Plugin
* [How I’m Using (New) Claude Code LSP to Code & Fix Bugs Faster (Language Server Protocol)](https://medium.com/@joe.njenga/how-im-using-new-claude-code-lsp-to-code-fix-bugs-faster-language-server-protocol-cf744d228d02)
* [I Tested All Available Claude Code LSP Plugins (Don’t Waste Time — Read This First)](https://medium.com/@joe.njenga/i-tested-all-available-claude-code-lsp-plugins-dont-waste-time-read-this-first-6896e992a540)

### Install Claude in Chrome
* [Claude in Chrome](https://chromewebstore.google.com/publisher/anthropic/u308d63ea0533efcf7ba778ad42da7390?pli=1)

### Install Cowork - NOT
Claude Cowork is a specialized "agentic" mode within the Claude Desktop application (available on Mac and Windows)
designed to act as an autonomous, tireless teammate for non-technical users.
Unlike the standard chat interface, where you have a back-and-forth conversation,
Cowork allows you to delegate complex, multi-step, or repetitive tasks directly to your local files and browser,
letting it work on its own while you focus on other things.

Unfortunately, **Claude Cowork does not support Ubuntu (Linux)**.
It's currently only available for macOS and Windows.
Cowork requires the Claude Desktop app for macOS or Windows and is not available on web, mobile, or Linux.
Linux is explicitly listed as "not currently supported" in Anthropic's documentation.
If you're on Linux and want to use Claude's agentic capabilities, Claude Code is your best alternative.
It's a CLI-based tool that runs in the terminal and supports Linux.
It offers similar autonomous, multi-step task execution but is geared more toward developers.

Available for Pro and Max plans, only on desktop, supporting macOS and Windows.
To install Claude Cowork, goto the [Downloads](https://claude.ai/downloads) page, and click on the **Cowork** button.

* [How Claude Cowork helps developers spread the AI knowledge](https://thenewstack.io/how-claude-cowork-helps-developers-spread-the-ai-knowledge/)
* [Claude COWORK Clearly Explained (& how to use it for beginners)](https://www.youtube.com/watch?v=ZeWfksNXlbU)

---------------

* [Claude vs. Gemini: Which one actually writes better code?](https://www.howtogeek.com/claude-vs-gemini-which-one-actually-writes-better-code/)
  * [Stop explaining context.](https://claude-mem.ai/)
  * [GitHub: anthropics/claude-code](https://github.com/anthropics/claude-code/tree/main/plugins)


Principles of Operation define the core rules, values, or fundamental truths guiding how a system or business behaves, focusing on how it should act.
Principles of Operation (Guiding Rules):
* Focus: Core values, behaviors, and rules (e.g., "be vision-driven," "customer first").
* Context: Used in business management and operational strategies to define culture and decision-making frameworks.
* Purpose: To guide how people or systems should operate to achieve consistent results.

Theory of Operation describes the technical, scientific, or functional "how and why" a system works, detailing its mechanics.
Principles guide decisions, while theories explain mechanisms
Theory of Operation (Technical Explanation):
* Focus: Technical, scientific, or functional mechanisms (e.g., "how a toaster works").
* Context: Used in engineering, product design, and documentation to explain the "how and why" of a system.
* Purpose: To describe the underlying principles of a specific device, component, or system's operation.


* Tips for writing good spec files
Your `spec.md` files can be as rough or as polished as you like — bullet points, prose, old emails, notes, whatever you have.
Claude will extract what's useful.
A minimal spec might look like:

```markdown
# Robotics for Kids — Course Notes
This is a makerspace course for kids & adults parents as a first introduction to robotics
- Ages 8–12, no prior experience
- 6 weeks, Saturday mornings, 2 hours each
- Using LEGO Mindstorms kits (we have 8 sets)
- Parents want kids to build AND program something by the end
- No soldering, nothing that needs a computer at home
```

That this may answer about half the questions, and Claude would only ask for the rest.

---------------

## Skill Plugins
Spec Kit and Superpowers represent two different approaches to managing AI coding agents.
Spec Kit focuses on how a project is planned and documented (spec-driven),
while Superpowers is an agentic skills framework that governs how the code is built and tested.

>**OpenSpec** is another Spec-Driven Development (SDD) frameworks designed to align AI coding tools.
>OpenSpec is best for lightweight, iterative tasks on existing codebases,
>while Spec Kit offers rigorous, gated workflows for comprehensive architectural planning.

**Spec Kit treats the specification as the source of truth; Superpowers treats the development workflow as the source of truth.**
* **Spec Kit**
  * Purpose: A spec-driven development (SDD) framework designed to document why changes are made and what the
    requirements are before any code is written.
  * Core Artifacts: Produces durable, human-readable markdown files like `spec.md` and `tasks.md`.
  * Workflow: You hand off structured spec templates to your AI agent so it knows exactly what features and file paths to target.
  * Best For: API design, spec-first development, and ensuring high architectural traceability
* **Superpowers**
  * Purpose: An agentic skills ecosystem focused on the actual execution quality of the code.
  * Workflow: Instead of needing a fully finished spec first, it features built-in skills like `/brainstorm`, `/plan`, and `/execute`.
  * Automation: It forces a strict "Red-Green" Test-Driven Development (TDD) loop, deploys sub-agents for parallel execution,
    and conducts automated code reviews before moving to the next task.
  * Best For: Complex codebases, updating multiple files simultaneously, and enforcing rigid testing protocols.


|  | Spec Kit | Superpowers |
|:-----:|:---------|:------------|
| Author / Owner | GitHub (org-backed) | Jesse Vincent + Prime Radiant team |
| Core idea | Specs are executable; code is generated from specs | Skills enforce a disciplined dev workflow |
| Primary artifact | The specification document | The skill (a triggered procedure) |
| Trigger model | User-invoked slash commands (/speckit.*) | Auto-triggered skills based on context |
| Methodology | Spec-Driven Development (SDD) | Agentic SDLC (brainstorm → design → plan → TDD → review → ship) |
| Best for | Greenfield features, brownfield enhancements, spec-to-code traceability | Multi-hour autonomous work, parallel subagents, TDD discipline |
| Distribution | Python CLI (uv tool install specify-cli) | Plugin marketplaces (Claude, Codex, Cursor, etc.) |
| License | MIT | MIT |
| Maturity | 90.8k stars, 136 releases, 100+ community extensions | 167k stars, active releases, Discord community |


* [Spec Kit vs. Superpowers — A Comprehensive Comparison & Practical Guide to Combining Both](https://viblo.asia/p/spec-kit-vs-superpowers-a-comprehensive-comparison-practical-guide-to-combining-both-13VM9DMxVY7)
* [OpenSpec VS SpecKit: Which AI Development Framework is Worth Your Time? Live Comparison](https://www.youtube.com/watch?v=xNOffgNnmWw)

To install

To disable or enable, use `/plugin disable superpowers` or `/plugin enable superpowers`.

### Pre-Installed Tools
* `update-config` — settings.json, hooks, permissions, env vars
* `keybindings-help` — customize keyboard shortcuts
* `verify` — run app and observe behavior
* `code-review` — review diff for bugs/cleanups
* `simplify` — simplify changed code
* `fewer-permission-prompts` — reduce permission prompts
* `loop` — run prompt on recurring interval
* `schedule` — scheduled remote agents / cron jobs
* `claude-api` — Claude API / Anthropic SDK apps
* `run` — launch and drive the app
* `init` — initialize CLAUDE.md
* `review` — review a pull request
* `security-review` — security review of pending changes

### [`superpowers`](https://github.com/obra/superpowers)
* `brainstorming` — before creative work / new features
* `dispatching-parallel-agents` — 2+ independent tasks
* `executing-plans` — run a written plan with review checkpoints
* `finishing-a-development-branch` — post-implementation integration options
* `receiving-code-review` — before implementing review feedback
* `requesting-code-review` — after completing tasks / before merging
* `subagent-driven-development` — execute plans with independent tasks
* `systematic-debugging` — any bug, test failure, unexpected behavior
* `test-driven-development` — before writing implementation code
* `using-git-worktrees` — isolate feature work
* `using-superpowers` — session start
* `verification-before-completion` — before claiming work is done
* `writing-plans` — multi-step tasks before touching code
* `writing-skills` — create/edit/verify skills

[Install the plugin][09] from Anthropic's official marketplace:
`/plugin install superpowers@claude-plugins-official`

* [Claude Code Now Has SUPERPOWERS! (plugin)](https://www.youtube.com/watch?v=vfVQP2AbUHo)
* [This One Plugin Just 10x’d Claude Code](https://www.youtube.com/watch?v=4XqVR6xI6Kw)
* [Claude Code + SUPERPOWERS = The End of Vibe Coding? (Full Tutorial)](https://www.youtube.com/watch?v=TX91PdBn_IA)

### [`spec-kit`](https://github.com/github/spec-kit)
To use Spec Kit with Claude Code on Ubuntu,
it is important to distinguish between the standalone Spec Kit CLI (the official, project-level tool)
and Claude Code Plugins (which may provide similar functionality).

The official Spec Kit approach is to install a dedicated CLI tool on your system and initialize it within your project.
This tool then interfaces with your AI coding agent (Claude Code).

Spec Kit ships as a small Python CLI named `specify`.
Install it once on your machine with `uv` or `uvx`:

```bash
# install the specify cli tool on you computer at ~/.local/bin/specify
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
# -- OR --
# an alternative is to place it within the project folder

#check where specify is located on you computer
$ which specify
/home/jeff/.local/bin/specify

# check the specify version
$ specify --version
specify 0.8.19.dev0

# remove the specify tool
uv tool uninstall specify-cli
```

Once initialized, you don't "install" Spec Kit into Claude Code like a plugin.
Instead, you use the specify CLI tools to prepare your environment,
and then use Claude Code to execute the resulting specifications.

```bash
# from inside the project directory where you want to use specify, initialize it
cd <project-directory>
specify init . --integration claude --script sh
# -- OR --
# to create the project directory
specify init <project-directory>  --integration claude --script sh
```

After the specify `init`, the projects filesystem is created and five slash commands appear in Claude Code's slash menu:
* `/speckit.constitution` — Establish project principles: Define project-wide non-negotiables
* `/speckit.specify` — Create baseline specification: Generate a feature spec from a natural-language description
* `/speckit.plan` — Create implementation plan: Generate the implementation plan from the spec and your tech constraints
* `/speckit.tasks` — Generate actionable tasks: Break the plan into an ordered list of tasks
* `/speckit.implement` — Execute implementation: Perform one or more tasks defined

Three additional helper scripts for review and refinement, but are optional:

* `/speckit.clarify` — Flags ambiguous requirements before they reach the plan:
  Ask structured questions to de-risk ambiguous areas before planning (run **before** `/speckit-plan` if used)
* `/speckit.analyze` — Cross-checks the spec against the plan and tasks for inconsistencies:
  Cross-artifact consistency & alignment report (**after** `/speckit-tasks`, but **before** `/speckit-implement`)
* `/speckit.checklist` — Generates review checklists you can hand to a human reviewer:
  Generate quality checklists to validate requirements completeness, clarity, and (**after** `/speckit-plan`)

To keep your Spec Kit workflow up to date,
you need to address two distinct components:
the global CLI tool and the project-specific files (templates, scripts, and slash commands).

```bash
# install latest upgrade
uv tool upgrade specify-cli

# to force a reinstall (useful if you want to pull the absolute latest from the git repository)
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

Updating the CLI tool does not automatically change the files inside your project directory (the `.specify/` folder).
To refresh your local project setup to match the new version of the CLI,
navigate to your project root and run: `specify init . --force --integration claude`.

>**Important Warning:**
>Running `specify init . --force` will overwrite your existing configuration files, including your `constitution.md`.
>
>**Recommended Workflow:**
>1. Back up your constitution:
> `cp .specify/memory/constitution.md .specify/memory/constitution-backup.md`
>1. Run the upgrade:
> `specify init . --force --integration claude`
>1. Restore your customizations:
> `mv .specify/memory/constitution-backup.md .specify/memory/constitution.md`
> (Alternatively, you can use `git restore .specify/memory/constitution.md` if you use version control).

* [Spec-Driven Development with Spec Kit and Claude Code](https://medium.com/vibecodingpub/spec-driven-development-with-spec-kit-and-claude-code-7e2957fd2c9b)
* [The ONLY guide you'll need for GitHub Spec Kit](https://www.youtube.com/watch?v=a9eR1xsfvHg)
* [GitHub Spec Kit Tutorials](https://www.youtube.com/playlist?list=PL4cUxeGkcC9h9RbDpG8ZModUzwy45tLjb)

---------------

## Don't Write Skills from Scratch
Use Anthropic's `/skill-creator` or SuperPower's `writing-skills`

* [Claude Skills 2.0: How to use Skill Creator to build new Skills](https://www.youtube.com/watch?v=rihf3-mpNG4)
* [Build Better AI Agent Skills With Skill Creator v2 from Anthropic](https://www.youtube.com/watch?v=WplS5lycPHM)

---------------



[01]:https://www.codecademy.com/article/how-to-build-claude-skills
[02]:https://code.claude.com/docs/en/overview
[03]:https://sc.edu/about/offices_and_divisions/cte/teaching_resources/syllabus_templates/
[04]:https://pub.spillwave.com/build-your-first-claude-code-skill-a-simple-project-memory-system-that-saves-hours-1d13f21aff9e
[05]:https://skillzwave.ai/ai-agent-guides/mastering-claude-skills-the-complete-guide-to-building-effective-agent-skills/
[06]:https://www.youtube.com/watch?v=vEvytl7wrGM
[07]:https://github.com/ShawhinT/ai-tutor-skill
[08]:https://agentskills.io/home
[09]:https://github.com/obra/superpowers

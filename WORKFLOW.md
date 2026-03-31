# 🧠 Plan → Build → Verify Workflow

A structured, multi-agent development workflow designed to maximize clarity, reduce token waste, and ensure high-quality outputs.

---

## 🎯 Core Principle

> Never mix planning, implementation, and verification in the same step.

Each phase has a dedicated role and tool.

---

## 🧩 Roles

### 🧠 Plan — ChatGPT (Strategist / Triage)
- Define tasks clearly
- Classify problem type
- Break down work into scoped units
- Write implementation briefs ("task packets")
- Identify root cause categories

### 🛠️ Build — Claude Code (Implementer)
- Make targeted, scoped changes
- Edit only specified files
- Avoid unnecessary refactors
- Return structured reports
- Optionally commit and push

### 🔍 Verify — Codex Plugin (Reviewer / Investigator)
- Review diffs against main
- Perform adversarial reviews
- Identify brittle logic or hidden risks
- Investigate bugs when results don’t match

---

## 🏷️ Task Classification

- FEATURE → New functionality  
- BUG → Something broken  
- ENV → Local setup issues  
- DEPLOY → CI/CD, GitHub Actions, Pages  
- REVIEW → Validation / QA  

Only ONE task class per request.

---

## 📦 Task Packet Template

TASK TYPE: [FEATURE | BUG | ENV | DEPLOY | REVIEW]

GOAL:
[Clear objective]

FILES ALLOWED:
[list]

DO NOT TOUCH:
[list]

SUCCESS CRITERIA:
- [outcome 1]
- [outcome 2]

OUTPUT FORMAT:
1. STATUS
2. FILES CHANGED
3. ROOT CAUSE
4. BEHAVIORAL IMPACT
5. NOT TOUCHED

---

## 🔄 Standard Workflow

1. Identify issue  
2. Classify task  
3. Create task packet  
4. Send to Claude Code  
5. Review with Codex  
6. Accept / refine / revert  

---

## 🧪 Codex Commands

/codex:review --base main --background  
/codex:adversarial-review --base main  
/codex:rescue investigate issue  
/codex:status  
/codex:result  

---

## 🚫 Anti-Patterns

- Mixing multiple task types  
- Vague “fix everything” prompts  
- Letting Claude scan entire repo  
- Debugging without isolating layer  
- Using one tool for everything  

---

## 🔍 Debug Layers

1. Code  
2. Environment  
3. Generated output  
4. Git state  
5. Deployment  
6. Cache  

---

## ⚙️ Golden Rules

- One task → one objective → one tool  
- Define success criteria first  
- Scope files  
- No unnecessary edits  
- Verify important changes  
- Separate workflows  
- Use fresh context when needed  

---

## 🚀 Summary

Plan → Build → Verify

Plan with clarity  
Build with precision  
Verify with skepticism  

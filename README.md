# Ara Paperwork Companion

Ara Paperwork Companion is a voice-driven tax document gatherer for Ara on macOS.
It helps Ara search Gmail for real tax-related attachments, scan local folders,
classify likely tax documents, and organize them into an accountant-ready folder.

## What It Does

- Uses Ara voice commands such as `Ara, gather everything I need for my taxes`.
- Guides Ara to search Gmail and download real tax attachments.
- Scans `~/Downloads/Ara Tax Inbox`, `~/Downloads`, `~/Documents`, and `~/Desktop`.
- Copies matching files into `~/Documents/Ara Paperwork/<tax-year>`.
- Categorizes documents into `Income`, `Donations`, `Investments`, `Medical`, and `Other`.
- Writes `summary.json` and `SUMMARY.txt`.

## Files

- `skills/ara-tax-gatherer/SKILL.md`: Ara skill instructions.
- `install_native_ara_skill.sh`: Installs the Ara skill into `~/.claude/skills`.
- `ara_native_handoff.sh`: One-command entrypoint used by Ara after Gmail downloads.
- `run_native_ara_tax_workflow.sh`: Builds the default local scan command.
- `ara_tax_helper.py`: Classifies, renames, copies, and summarizes documents.

## Install

```bash
"/Users/saitejadesu/Personal/Open Source/ai-paperwork-companian/install_native_ara_skill.sh"
```

Restart Ara after installing if it does not pick up the skill immediately.

## Voice Usage

Say:

```text
Ara, gather everything I need for my taxes
```

For a specific year:

```text
Ara, gather everything I need for my 2024 taxes
```

## Local Command

Ara should run this after attempting Gmail attachment downloads:

```bash
"/Users/saitejadesu/Personal/Open Source/ai-paperwork-companian/ara_native_handoff.sh"
```

For a specific year:

```bash
"/Users/saitejadesu/Personal/Open Source/ai-paperwork-companian/ara_native_handoff.sh" --year 2024
```

## Boundaries

This project gathers and organizes documents only. It does not file taxes,
calculate taxes, or provide tax, legal, financial, or medical advice.

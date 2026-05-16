# Ara Paperwork Companion

Ara Paperwork Companion is a small local workflow for Ara on macOS. It helps
Ara gather real tax documents, organize them by year and category, and create a
short summary you can share with an accountant.

## What It Does

When you ask Ara to gather tax documents, this workflow tells Ara to:

- Search Gmail for likely tax forms and receipts.
- Download real tax-related attachments.
- Scan common local folders on your Mac.
- Copy matching files into one organized tax folder.
- Rename files into a consistent format.
- Write a JSON summary and a readable text summary.

The output folder is:

```text
~/Documents/Ara Paperwork/<tax-year>
```

Inside it, files are grouped into:

- `Income`
- `Donations`
- `Investments`
- `Medical`
- `Other`

## How It Works With Ara

This repo provides an Ara skill plus a local helper script.

Ara handles the voice and Gmail parts:

- Understands your voice command.
- Searches Gmail.
- Downloads matching attachments.
- Runs the local workflow command.

The local helper handles file organization:

- Scans `~/Downloads/Ara Tax Inbox`.
- Scans `~/Downloads`, `~/Documents`, and `~/Desktop`.
- Classifies likely tax documents.
- Copies and renames matches.
- Opens the organized folder.
- Speaks a short completion summary.

## Install

1. Install and open Ara for macOS.

2. Make sure Ara has access to Gmail and local files. The workflow works best
   when Ara can search Gmail, download attachments, and run local shell
   commands.

3. Clone this repo:

```bash
git clone https://github.com/desusaiteja/ai-paperwork-companian.git
cd ai-paperwork-companian
```

4. Install the Ara skill:

```bash
"./install_native_ara_skill.sh"
```

This installs the Ara skill into:

```text
~/.claude/skills/ara-tax-gatherer/SKILL.md
```

Restart Ara after installing so it can load the skill.

## Replicate The Ara Setup

To use this workflow on another Mac:

1. Clone this repo on that Mac.
2. Run `./install_native_ara_skill.sh`.
3. Restart Ara.
4. Sign in to Gmail in the browser/account Ara uses.
5. Give Ara permission to download files and access local folders if macOS asks.
6. Say `Ara, gather everything I need for my taxes`.

Ara should then follow the installed skill:

- Search Gmail with tax-document queries.
- Download matching attachments.
- Save them to `~/Downloads/Ara Tax Inbox` when possible.
- Run `./ara_native_handoff.sh`.
- Organize matches into `~/Documents/Ara Paperwork/<tax-year>`.

If Ara finds emails but does not download attachments, the local helper can only
organize files that already exist on the Mac. The Gmail download step is the
part Ara must perform.

## Use With Ara Voice

Say:

```text
Ara, gather everything I need for my taxes
```

For a specific year, say:

```text
Ara, gather everything I need for my 2024 taxes
```

Ara should search Gmail, download matching attachments, and then run the local
handoff command:

```bash
"./ara_native_handoff.sh"
```

For a specific year, Ara can run:

```bash
"./ara_native_handoff.sh" --year 2024
```

## What Gmail Searches For

The skill asks Ara to look for common tax documents such as:

- W-2 forms
- 1099 forms
- 1099-INT bank interest statements
- 1099-DIV and brokerage statements
- 1098 mortgage interest forms
- Donation receipts
- Medical, dental, pharmacy, HSA, and FSA receipts
- Year-end financial statements

Downloaded attachments should go into:

```text
~/Downloads/Ara Tax Inbox
```

If Gmail saves them to the normal Downloads folder instead, that is fine. The
helper scans both locations.

## Run The Local Workflow Manually

You can also run the local organizer yourself:

```bash
"./ara_native_handoff.sh"
```

For a specific year:

```bash
"./ara_native_handoff.sh" --year 2024
```

This does not search Gmail by itself. It only scans local files that already
exist on your Mac.

## Troubleshooting

- If Ara does not trigger the skill, restart Ara and say the command again.
- If no files are gathered, check whether Gmail attachments were actually downloaded.
- If Gmail downloads to `~/Downloads` instead of `~/Downloads/Ara Tax Inbox`, that is okay.
- If macOS blocks folder access, allow Ara or the terminal app to access Downloads, Documents, and Desktop.
- If you only run `./ara_native_handoff.sh`, Gmail is not searched. That command only organizes local files.

## Important Notes

- This project does not file taxes.
- This project does not calculate taxes.
- This project does not provide tax, legal, financial, or medical advice.
- It only gathers, copies, renames, organizes, and summarizes documents.

## Project Files

- `skills/ara-tax-gatherer/SKILL.md`: Instructions Ara reads for the voice workflow.
- `install_native_ara_skill.sh`: Installs the Ara skill locally.
- `ara_native_handoff.sh`: Entry point Ara runs after Gmail downloads.
- `run_native_ara_tax_workflow.sh`: Builds the default scan command.
- `ara_tax_helper.py`: Classifies and organizes files.

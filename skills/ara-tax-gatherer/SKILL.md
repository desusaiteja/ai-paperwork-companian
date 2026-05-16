---
name: ara-tax-gatherer
description: Use immediately when the user says "Ara, gather everything I need for my taxes", "Ara, gather my tax documents", "Ara, collect my tax paperwork", "Ara, find my tax forms", "Ara, organize my tax files", or any tax-document gathering request. This skill performs a real Gmail/download/local-folder workflow and must not use mock data.
---

# Ara Tax Gatherer

This is a real voice-command execution skill. The user wants Ara to gather real files now.

## Critical Rules

- Do not use mock data.
- Do not ask the user what to do next.
- Do not ask where to search.
- Do not offer buttons such as "Open Tax folder", "List recent files", or "Check email for forms".
- Do not stop after scanning emails.
- Do not claim success until the local helper command has run and printed JSON.

## Required Workflow

### 1. Determine tax year

If the user says a year like `2024`, use that year. If no year is specified, use the prior calendar year.

### 2. Search Gmail and download real attachments

Create this staging folder if needed:

```bash
mkdir -p "$HOME/Downloads/Ara Tax Inbox"
```

Search Gmail for likely tax attachments. Use the selected tax year in the queries.

Core searches:

```text
filename:pdf <tax-year> ("W-2" OR W2)
filename:pdf <tax-year> 1099
filename:pdf <tax-year> ("1099-INT" OR "interest statement" OR "bank interest")
filename:pdf <tax-year> ("1099-DIV" OR "1099-B" OR "consolidated 1099" OR brokerage)
filename:pdf <tax-year> ("1099-NEC" OR "1099-MISC" OR "1099-K")
filename:pdf <tax-year> (1098 OR "mortgage interest")
filename:pdf <tax-year> ("tax form" OR "tax document" OR "tax statement")
filename:pdf <tax-year> ("donation receipt" OR "charitable receipt" OR charity OR donor)
filename:pdf <tax-year> (medical OR dental OR hospital OR clinic OR pharmacy)
filename:pdf <tax-year> (HSA OR FSA OR copay OR deductible)
filename:pdf <tax-year> ("year end statement" OR "year-end statement")
filename:pdf <tax-year> (Vanguard OR Fidelity OR Schwab OR "Charles Schwab" OR Robinhood)
filename:pdf <tax-year> ("Bank of America" OR Chase OR Wells Fargo OR Citi)
```

Date-window searches:

```text
after:<tax-year>/01/01 before:<tax-year + 1>/01/01 filename:pdf 1099
after:<tax-year + 1>/01/01 before:<tax-year + 1>/05/01 filename:pdf 1099
after:<tax-year>/01/01 before:<tax-year + 1>/01/01 filename:pdf ("donation receipt" OR medical OR dental)
after:<tax-year + 1>/01/01 before:<tax-year + 1>/05/01 filename:pdf ("W-2" OR "1099-INT" OR "1099-DIV" OR 1098)
```

Open matching Gmail messages and download every likely tax-related attachment with extension `.pdf`, `.png`, `.jpg`, `.jpeg`, `.csv`, or `.txt`.

Prefer saving attachments into:

```text
~/Downloads/Ara Tax Inbox
```

If Gmail saves to the normal Downloads folder instead, continue. The helper scans `~/Downloads`.

### 3. Run the real local workflow

After attempting Gmail downloads, immediately use Ara's local shell/Bash command tool.

If no year was specified, run:

```bash
"/Users/saitejadesu/Personal/Open Source/ai-paperwork-companian/ara_native_handoff.sh"
```

If the user includes a year like `2024`, run:

```bash
"/Users/saitejadesu/Personal/Open Source/ai-paperwork-companian/ara_native_handoff.sh" --year 2024
```

This scans real local folders:

- `~/Downloads/Ara Tax Inbox`
- `~/Downloads`
- `~/Documents`
- `~/Desktop`

It organizes matches into:

```text
~/Documents/Ara Paperwork/<tax-year>
```

## After The Command Finishes

Read the JSON printed by the command.

Tell the user:

`I gathered <documentsFound> tax-related documents and organized them in <outputFolder>.`

If `missingLikely` has entries, add:

`You may still be missing <first missing item>.`

## Boundaries

- Do not file taxes.
- Do not calculate taxes.
- Do not give tax, legal, financial, or medical advice.
- Only gather, classify, rename, copy, organize, summarize, and open the result folder.

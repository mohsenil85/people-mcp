# Tutorial: Your First Job Application with people-mcp

This tutorial walks you through a complete job application workflow — from installation to interview prep. By the end, you'll have saved a job posting, tailored a resume, run a mock interview, and cleaned up.

Every step shows what you say to Claude, what happens behind the scenes, and what comes back.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- A LaTeX distribution with `lualatex` (for resume compilation)
- A workspace directory containing your `resume.tex`

## Step 1: Install and configure

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd people-mcp
uv sync
```

Add people-mcp to your Claude Code MCP config (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "people": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/people-mcp", "people-mcp"],
      "env": {
        "PEOPLE_WORKSPACE": "/Users/you/Projects/resume"
      }
    }
  }
}
```

Set `PEOPLE_WORKSPACE` to a directory containing your base `resume.tex`. This is your workspace root — people-mcp reads your profile from here and creates company subdirectories for each application.

Restart Claude Code to pick up the new server.

## Step 2: Verify your profile

Let's confirm people-mcp can read your resume.

**You say:**
> Read my professional profile.

**What happens:** Claude calls `get_profile`, which reads `resume.tex` from your workspace root.

**What comes back:** The full content of your `resume.tex` file. Claude can now reference your skills, experience, and education in all subsequent interactions.

## Step 3: Save a job posting

You've found a role at Stripe. Let's save the posting.

**You say:**
> Save this job posting for Stripe: https://stripe.com/jobs/listing/engineer

**What happens:** Claude calls `save_job_posting` with `company="Stripe"` and `url="https://stripe.com/jobs/listing/engineer"`. The server:
1. Sanitizes "Stripe" → `stripe`
2. Fetches the URL with httpx
3. Strips HTML tags from the response
4. Creates `$PEOPLE_WORKSPACE/stripe/` if it doesn't exist
5. Writes the text to `stripe/job_posting.md`

**What comes back:** `"Saved job_posting.md for stripe"`

If the posting is behind a login wall, paste the text instead:

**You say:**
> Save this job posting for Stripe:
> [paste the posting text here]

Claude will pass the text as `content` instead of `url`.

## Step 4: Research the company

Ask Claude to research Stripe and save notes.

**You say:**
> Research Stripe — their engineering culture, tech stack, and recent news. Save your findings.

**What happens:** Claude searches the web, synthesizes its findings, then calls `save_application_file` with `company="Stripe"`, `filename="company_research.md"`, and the research content.

**What comes back:** `"Saved company_research.md for stripe"`. You now have:

```
stripe/
├── job_posting.md
└── company_research.md
```

## Step 5: Develop a strategy

**You say:**
> Based on my profile and this role, write an application strategy.

**What happens:** Claude calls `get_profile` to review your resume, then `get_application` to read all Stripe materials. It reasons about the fit and calls `save_application_file` with `filename="META.md"` containing the strategy.

**What comes back:** `"Saved META.md for stripe"`

## Step 6: Tailor your resume

**You say:**
> Tailor my resume for this Stripe role. Emphasize distributed systems and API design.

**What happens:** Claude reads your base `resume.tex`, reads the job posting and strategy, then calls `save_application_file` with `filename="resume.tex"` — writing a tailored version into the Stripe directory.

**What comes back:** `"Saved resume.tex for stripe"`

## Step 7: Compile the resume

**You say:**
> Compile my Stripe resume.

**What happens:** Claude calls `compile_resume` with `company="Stripe"`. The server runs `lualatex -interaction=nonstopmode resume.tex` in the `stripe/` directory.

**What comes back:** The compilation output and the path to `stripe/resume.pdf`. If there are LaTeX errors, Claude will see them and can help fix your `.tex` file.

## Step 8: Run a mock interview

Time to practice. Let's do a behavioral interview.

**You say:**
> Run a mock behavioral interview for Stripe.

**What happens:** Claude calls `mock_interview` with `company="Stripe"` and `interview_type="behavioral"`. The server:
1. Gathers all text files from the `stripe/` directory
2. Verifies a job posting exists
3. Reads your profile
4. Returns a briefing with interviewer guidance, your profile, and all materials

**What comes back:** Claude switches into interviewer mode. It has the job posting, your resume, company research, and specific guidance for behavioral interviews (STAR method, probing follow-ups, etc.). It will ask you questions and evaluate your answers.

After the interview, Claude may save feedback:

**You say:**
> Save the feedback from that interview.

Claude calls `save_application_file` with `filename="interview_feedback.md"`.

## Step 9: Review your application

Check what you've built:

**You say:**
> Show me all my applications.

**What happens:** Claude calls `list_applications`, which scans the workspace for subdirectories and lists their files.

**What comes back:**
```
stripe:
  - company_research.md
  - interview_feedback.md
  - job_posting.md
  - META.md
  - resume.tex
```

To read a specific file:

**You say:**
> Show me my Stripe strategy.

Claude calls `read_application_file` with `company="Stripe"` and `filename="META.md"`.

## Step 10: Clean up

After you've applied (or decided not to):

**You say:**
> Delete the Stripe application.

**What happens:** Claude calls `delete_application` with `company="Stripe"`. The server removes the entire `stripe/` directory.

**What comes back:** `"Deleted application: stripe"`

## What's next

- Try different interview types: `technical`, `culture`, `manager`
- Save cover letters as `coverletter.txt`
- Store any file you want — there's no whitelist on filenames
- Read the [how-to guides](how-to.md) for focused recipes
- Check the [reference](reference.md) for complete tool documentation

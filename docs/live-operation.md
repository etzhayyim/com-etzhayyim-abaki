# Itonami deployment and periodic publication

The runtime profile is `abaki` in the owner's existing Hermes profile directory.
The initial run may be dispatched by Itonami's existing gateway. Long pre-run
scripts are synchronous there, so deployment uses the dedicated
`cloud.itonami.bot.abaki` launchd dispatcher afterward: it calls
`itonami-agent -p abaki cron tick --force` every minute. The profile records
`:runtime {:engine :itonami-agent :scheduler :launchd}`; the shared gateway skips
it, and Hermes' parked marker prevents a second engine from ticking it. `--force`
delegates only the due-check to this declared dispatcher; it grants no tools or
publication authority. Existing per-profile locks and next_run_at prevent double
dispatch. Other profile services are never restarted. A job runs
every 6 hours, one relevant-market discovery or overdue-case refresh per run.
The initial discovery starts at JP / information and communication; subsequent
discoveries rotate through geographic scopes within each industry. The cursor
is public in research-progress.json and advances only as part of a publication.
A case or a discovery attempt never establishes whole-region/industry coverage.

The scheduled profile script calls the pinned owner `scripts/live_tick.py` with
a host-only execution.json specifying `agent_bin`, `publication`, `staging` and
`state` absolute paths. Use dedicated publication and proposal workspaces under
the github forest. The publication worktree must use branch `abaki-reports` and
remote `etzhayyim/com-etzhayyim-abaki`; it cannot carry unrelated WIP.

The research turn runs through Itonami agent using a staging cwd, only web/file
tools, 18 tool calls / 900 seconds requested, and a runtime turn/budget limit.
Credentials remain in the profile's existing host storage. The researcher cannot
publish through terminal tools. A host publisher validates the proposal, fetches
each public original over HTTPS (DNS pinned at connect, redirects rechecked,
no private hosts/proxies, 2 MiB cap), and requires its short verbatim supporting
excerpt to occur in the original. This establishes source readback, not an
independent legal adjudication or proof of every semantic inference.

The trusted script builds reports using the owner validator and commits/pushes
only reports, evidence/cases and research-progress.json to `abaki-reports`.
It never pushes main, force-pushes, merges PRs, or broadcasts a supplier blocklist.
Publication is a public repository artifact at:

https://github.com/etzhayyim/com-etzhayyim-abaki/tree/abaki-reports/reports

The returned immutable commit and key files are independently fetched from
GitHub and byte-compared. Host receipts record research outcome, source hashes,
parent process ID, source pipeline commit, public commit and readback hashes.
The wrapper returns `wakeAgent:false` after this complete research/publication
cycle to prevent the cron engine starting a redundant second agent turn.

Failure does not advance the published cursor. A dirty worktree, inaccessible
source, absent quote, invalid case or failed model call refuses publication.
If a push/readback fails after the commit exists locally, recover that report-only
commit and verify it remotely before the next run; the pipeline refuses to begin
new research with a pending unpublished commit. Retain failed receipts and notify
the operator; do not relabel a failed run as completed.

The existing native Itonami Marketplace already carries the owner role. Install
it in the human's organization and use its persistent SOUL to point at this
profile scheduler and published report surface; do not start duplicate native
research schedules against the same cursor. Marketplace presence, host profile
adoption, scheduler dispatch, model execution and public readback are separate
deployment checks.

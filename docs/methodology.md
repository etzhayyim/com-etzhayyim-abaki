# Evidence and publication contract

The unit is region × relevant market × observation period. ISIC sections only
organize discovery; substitution and competitive conditions define the actual
market. Corporate domicile is not the geographic market. Brand/subsidiary shares
must be aggregated into independent control groups. Consider supply, demand,
entry barriers, buyer power and public/statutory exclusive rights.

Classifications:

- `court-confirmed-monopoly`: specifically attributed court finding, official
  evidence, case identifier, court, decision date and unresolved/final appeal state.
- `authority-confirmed-dominance`: attributed competition-authority decision;
  dominance alone is not prohibited conduct.
- `authority-described-oligopoly`: attributed official market-structure finding;
  no automatic inference of collusion or illegality.
- `authority-confirmed-exclusionary-conduct`: attributed official exclusionary
  or unfair-practice finding relevant to competitive barriers; it does not by
  itself establish a monopoly, dominant position or an exact market share.
- `concentration-screen`: analyst calculation, never a legal determination.
- `insufficient-evidence`: retain gaps and competing market definitions.

Sources include title, publisher, kind, public HTTPS URL, exact locator,
publication/access dates, and claim-level references. The validator establishes
structural linkage, not the truth of source contents: the research bot must read
the original source, reconcile contrary evidence and independently verify every
claim before publication. The repository examples were read from official DOJ,
ACCC and European Commission pages on 2026-10-13. They establish historical
findings, not present worldwide market power or appellate finality.

HHI = sum of squared percentage shares (0..10000). For incomplete shares report
the observed sum of squares as a lower bound and add squared residual for a
conservative upper bound. Do not treat that upper bound as measured HHI. Exact
CR2/CR4 require a complete distribution; otherwise report observed top-2/top-4
lower bounds. None of these metrics alone proves monopoly or abuse. Share units,
periods and denominators must match. Duplicate control groups are refused.

Publish reports/README.md, findings.json, coverage.json, individual reports and
artifact receipt as a single reviewed repository change. Git commit history is
the version trail; verify remote bytes at the published immutable commit. The
builder's receipt records generation only and cannot assert remote publication.
Reports show reviewed_on, review_due and historical/overdue freshness. Re-read
sources, appeal dockets, company responses and corrected statistics each cycle;
never advance reviewed_on solely because the builder ran.

Corrections must name a case ID, affected claim and primary source. Correct the
evidence, rebuild and publish a superseding commit; retain previous versions in
Git. Removing a case must also remove its generated Markdown report in the same
reviewed change. Never merge stale artifacts left over from removed inputs.

The global queue is coverage accounting, not an autonomous crawler or continuous
deployment. Scheduling and model/web tool binding belong to the installed host.
Legacy abaki react-router and live-gate remain separate from this report pipeline.

# abaki（暴）— Itonami Global Market Watch

An Itonami bot profile and executable evidence/report pipeline for identifying
real organizations' monopoly, oligopoly and market concentration by region,
relevant market and period. The canonical profile is
[hermes/profiles/abaki](hermes/profiles/abaki). [Published reports](reports/README.md)
include Japanese/English findings, primary sources and explicit coverage gaps.

```sh
python3 scripts/market_watch.py queue --region JP --industry J --limit 10
python3 scripts/market_watch.py validate --as-of 2026-10-13
python3 scripts/market_watch.py build --as-of 2026-10-13
python3 -m unittest discover -s tests -v
```

The CLI uses the Python 3 standard library and reads evidence/cases/*.json.
Research uses the profile's host-bound web tools; provider credentials and tool
permissions stay on the host. The profile description follows Itonami's existing
Hermes profile format; config.yaml is an inert scaffold until bound to a host.
Register/discover the role through Itonami's registry and public bot catalog.
Installing a catalog entry creates a fresh bot and does not copy credentials,
conversations or signer authority.

Scope: 249 ISO country/territory entries from public-domain IANA tzdb, plus EEA
and WORLD, × 21 UN ISIC Rev.4 sections. Names and source digest are pinned in
evidence/coverage-catalog.json. This is a finite research queue, not a claim to
have analyzed all markets. Subnational areas and actual relevant markets are
explicit additional definitions. Missing cases remain `unresearched`.

Initial real cases: US general search (Google), Australian supermarket retailing
(Woolworths, Coles, ALDI), and EEA publisher ad servers (Google). These are
attributed historical findings; current appeal status is explicitly unresolved.
There are no compatible individual share observations in these initial cases,
so the report does not fabricate HHI/CR values.

See [methodology](docs/methodology.md). The old trait-weighted analysis and
data/seed.edn remain legacy simulation fixtures. The new reporting pipeline
does not produce a supplier blocklist, call mesh, or bypass the existing
member-signed outward-action gate. Repository publication happens through
authorized commits/PRs; local artifact receipts explicitly say unpublished.

#!/usr/bin/env python3
"""Evidence-bound market observation. Standard library only; no implicit network or grants."""
import argparse
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CLASSES = {"court-confirmed-monopoly", "authority-confirmed-dominance",
           "authority-described-oligopoly", "authority-confirmed-exclusionary-conduct",
           "concentration-screen", "insufficient-evidence"}


def load(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def day(value):
    return dt.date.fromisoformat(value)


def validate(case, catalog, today):
    require(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}", case["id"]), "invalid case id")
    require(case["region"] in catalog["regions"], "unknown region; extend coverage catalog first")
    require(case["industry"] in catalog["industries"], "unknown industry")
    for field in ("market", "geographic_scope", "period", "denominator", "limitations"):
        require(isinstance(case[field], str) and case[field].strip(), "missing " + field)
    require(case["classification"] in CLASSES, "unknown classification")
    require(day(case["reviewed_on"]) <= today, "future review date")
    require(isinstance(case["review_after_days"], int) and 1 <= case["review_after_days"] <= 366,
            "invalid review interval")
    sources = {s["id"]: s for s in case["sources"]}
    require(len(sources) == len(case["sources"]) and bool(sources), "missing or duplicate sources")
    for source in sources.values():
        url = urlsplit(source["url"])
        require(url.scheme == "https" and bool(url.hostname) and not url.username and not url.password,
                "source must be a public HTTPS URL")
        require(source["kind"] in {"court", "competition-authority", "official-statistics", "filing", "secondary"},
                "unknown source kind")
        for field in ("publisher", "title", "locator"):
            require(isinstance(source[field], str) and source[field].strip(), "missing source " + field)
        require(day(source["published_on"]) <= day(source["accessed_on"]) <= today,
                "invalid source dates")
    def cited(refs):
        require(bool(refs) and set(refs) <= sources.keys(), "unresolved or absent evidence")
    require(bool(case["entities"]), "no real organizations")
    entity_ids = set()
    for entity in case["entities"]:
        require(entity["id"] not in entity_ids, "duplicate organization/control group")
        entity_ids.add(entity["id"])
        require(bool(entity["name"].strip()) and bool(entity["identity_url"].strip()), "missing organization identity")
        require(urlsplit(entity["identity_url"]).scheme == "https", "invalid organization identity URL")
        require(bool(entity["control_group"].strip()), "missing control group")
        cited(entity["source_refs"])
    require(bool(case["claims"]), "no evidenced claims")
    for claim in case["claims"]:
        require(bool(claim["text"].strip()), "empty claim")
        cited(claim["source_refs"])
    cited(case["classification_refs"])
    legal = case["legal_status"]
    require(legal["finality"] in {"not-assessed", "pending", "appealable", "final", "unknown"}, "unknown legal finality")
    require(bool(legal["note"].strip()), "missing legal status caveat")
    if case["classification"] != "concentration-screen" and case["classification"] != "insufficient-evidence":
        basis = case["classification_basis"]
        cited(basis["source_refs"])
        require(bool(basis["authority"].strip()) and bool(basis["finding"].strip()), "missing attributed finding")
        require(day(basis["decision_date"]) <= today, "future decision")
        kinds = {sources[s]["kind"] for s in basis["source_refs"]}
        require(bool(kinds & {"court", "competition-authority"}), "classification needs official finding")
        require(set(basis["source_refs"]) <= set(case["classification_refs"]), "finding absent from classification evidence")
        if case["classification"] == "court-confirmed-monopoly":
            require(legal["case_id"].strip(), "missing court case reference")
            require(bool(basis.get("court_name", "").strip()), "missing court attribution")
    shares = case.get("shares", [])
    require(type(case.get("shares_complete", False)) is bool, "shares_complete must be boolean")
    groups = set()
    for item in shares:
        require(item["entity_id"] in entity_ids, "share without real entity")
        group = next(e["control_group"] for e in case["entities"] if e["id"] == item["entity_id"])
        require(group not in groups, "aggregate controlled subsidiaries before measuring")
        groups.add(group)
        value = item["percent"]
        require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 100, "invalid share")
        cited(item["source_refs"])
        require(item["period"] == case["period"] and item["denominator"] == case["denominator"],
                "incompatible share periods or denominators")
    require(sum(s["percent"] for s in shares) <= 100.000001, "shares exceed 100%")
    if case.get("shares_complete"):
        require(shares and abs(sum(s["percent"] for s in shares) - 100) < 0.000001, "incomplete shares marked complete")
    if case["classification"] == "concentration-screen":
        require(bool(shares), "concentration screen requires shares")
    return case


def metrics(case):
    shares = sorted((s["percent"] for s in case.get("shares", [])), reverse=True)
    if not shares:
        return {"hhi": None, "cr2": None, "cr4": None, "note": "Shares unavailable; no numeric estimate."}
    lower = sum(s*s for s in shares)
    residual = max(0, 100 - sum(shares))
    complete = case.get("shares_complete", False)
    return {"hhi": round(lower, 4) if complete else None,
            "hhi_bounds": [round(lower, 4), round(lower + residual*residual, 4)],
            "observed_share_total": round(sum(shares), 4),
            "cr2": round(sum(shares[:2]), 4) if complete else None,
            "cr4": round(sum(shares[:4]), 4) if complete else None,
            "observed_top2_lower_bound": round(sum(shares[:2]), 4),
            "observed_top4_lower_bound": round(sum(shares[:4]), 4),
            "note": "Incomplete shares yield bounds, not an exact HHI/CR or legal verdict. Residual is not one assumed firm."}


def assess(case, today):
    result = dict(case)
    result["metrics"] = metrics(case)
    due = day(case["reviewed_on"]) + dt.timedelta(days=case["review_after_days"])
    result["review_due"] = due.isoformat()
    result["freshness"] = "review-overdue" if today > due else "reviewed-historical-snapshot"
    result["input_sha256"] = hashlib.sha256(json.dumps(case, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return result


def markdown(case):
    text = [f'# {case["id"]}', '', f'市場 / Market: {case["market"]}',
            f'地域 / Geography: {case["geographic_scope"]} ({case["region"]})',
            f'期間 / Period: {case["period"]}; denominator: {case["denominator"]}', '',
            f'分類 / Classification: **{case["classification"]}**',
            f'確認日: {case["reviewed_on"]}; 次回確認: {case["review_due"]}; {case["freshness"]}', '',
            '## Organizations / 組織', '']
    text += [f'- [{e["name"]}]({e["identity_url"]}) — control group: {e["control_group"]}; evidence: {", ".join(e["source_refs"])}'
             for e in case["entities"]]
    text += ['', '## Findings / 根拠付き分析', '']
    sources = {s["id"]: s for s in case["sources"]}
    for claim in case["claims"]:
        links = ', '.join(f'[{ref}]({sources[ref]["url"]})' for ref in claim["source_refs"])
        text.append(f'- {claim["text"]} ({links})')
    if case.get('classification_basis'):
        text += ['', 'Attribution: ' + json.dumps(case['classification_basis'], ensure_ascii=False)]
    text += ['', '## Concentration / 市場集中', '', '```json',
             json.dumps(case["metrics"], ensure_ascii=False, indent=2), '```', '',
             '## Legal status and limits / 法的状態・限界', '',
             f'Finality: {case["legal_status"]["finality"]}. {case["legal_status"]["note"]}',
             case['limitations'], '', 'Market concentration alone does not establish unlawful conduct.', '',
             '## Sources / 一次資料', '']
    text += [f'- [{s["id"]}: {s["title"]}]({s["url"]}) — {s["publisher"]}, {s["kind"]}; '
             f'published {s["published_on"]}; accessed {s["accessed_on"]}; locator: {s["locator"]}'
             for s in case["sources"]]
    text += [f'  Verified source excerpt: “{s["supporting_excerpt"]}”' for s in case["sources"] if s.get('supporting_excerpt')]
    text += ['', f'Input SHA-256: `{case["input_sha256"]}`', '']
    return '\n'.join(text)


def build(input_dir, output_dir, catalog, today):
    cases = [validate(load(p), catalog, today) for p in sorted(Path(input_dir).glob('*.json'))]
    require(bool(cases), 'no evidence cases')
    require(len({c['id'] for c in cases}) == len(cases), 'duplicate case id')
    results = [assess(c, today) for c in cases]
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    def write(name, data):
        (out / name).write_text(data)
    def json_write(name, value):
        write(name, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    json_write('findings.json', {'schema': 'abaki.findings.v1', 'as_of': today.isoformat(), 'findings': results})
    observed = {(c['region'], c['industry']) for c in cases}
    cells = [{'region': r, 'industry': i, 'status': 'has-evidence-case' if (r,i) in observed else 'unresearched'}
             for r in catalog['regions'] for i in catalog['industries']]
    json_write('coverage.json', {'schema': 'abaki.coverage.v1', 'as_of': today.isoformat(),
                              'note': 'A case does not qualify an entire country/industry. Unresearched never means competitive.',
                              'case_count': len(cases), 'cells': cells})
    for case in results:
        write(case['id'] + '.md', markdown(case))
    lines = ['# abaki — Global Market Watch / 世界の独占・寡占観測', '',
             f'As of {today.isoformat()}. {len(cases)} evidenced market cases; '
             f'{len(catalog["regions"])} regions × {len(catalog["industries"])} industry sections in the research queue.', '',
             'These are attributed historical findings, not a statement that every region has been researched.', '',
             '| Region | Market | Classification | Report |', '|---|---|---|---|']
    lines += [f'| {c["region"]} | {c["market"]} | {c["classification"]} | [{c["id"]}]({c["id"]}.md) |' for c in results]
    lines += ['', '[Machine-readable findings](findings.json) · [Coverage and gaps](coverage.json)', '',
              'Corrections: open an issue with a case ID, official source and affected statement. '
              'Superseded findings remain in Git history. Publication is a repository commit; '
              'this builder neither signs nor broadcasts the legacy route-around blocklist.', '']
    write('README.md', '\n'.join(lines))
    names = ['README.md', 'findings.json', 'coverage.json'] + [c['id'] + '.md' for c in results]
    json_write('receipt.json', {'schema': 'abaki.artifact-receipt.v1', 'as_of': today.isoformat(),
                              'state': 'generated-local-artifacts', 'remote_publication_verified': False,
                              'files': {name: hashlib.sha256((out/name).read_bytes()).hexdigest() for name in names}})
    return results


def queue(catalog, region=None, industry=None, limit=10, findings=(), today=None):
    require(region is None or region in catalog['regions'], 'unknown queue region')
    require(industry is None or industry in catalog['industries'], 'unknown queue industry')
    require(1 <= limit <= 100, 'queue limit must be 1..100')
    # One studied relevant market never removes an entire industry from discovery.
    # Overdue cases are refreshed first; ongoing discovery remains visible afterward.
    overdue = [c for c in findings if today and today > day(c['reviewed_on']) + dt.timedelta(days=c['review_after_days'])]
    rows = []
    for case in overdue:
        if (region and region != case['region']) or (industry and industry != case['industry']):
            continue
        rows.append({'region': case['region'], 'industry': case['industry'], 'case_id': case['id'],
                     'status': 'review-overdue', 'queries': [case['market'] + ' appeal remedies latest market shares'],
                     'instruction': 'Refresh this specific case without extrapolating to the whole industry.'})
        if len(rows) >= limit:
            return rows
    for r, name in catalog['regions'].items():
        for i, sector in catalog['industries'].items():
            if (region and region != r) or (industry and industry != i):
                continue
            rows.append({'region': r, 'industry': i, 'status': 'research-required',
                         'queries': [f'{name} {sector} competition authority market study market shares',
                                     f'{name} {sector} monopoly oligopoly court decision'],
                         'instruction': 'Use local-language primary sources; define a relevant market and period before creating a case.'})
            if len(rows) >= limit:
                return rows
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['validate', 'build', 'queue'])
    parser.add_argument('--input', type=Path, default=ROOT/'evidence/cases')
    parser.add_argument('--output', type=Path, default=ROOT/'reports')
    parser.add_argument('--catalog', type=Path, default=ROOT/'evidence/coverage-catalog.json')
    parser.add_argument('--as-of', default=dt.date.today().isoformat())
    parser.add_argument('--region')
    parser.add_argument('--industry')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    today, catalog = day(args.as_of), load(args.catalog)
    if args.command == 'queue':
        cases = [validate(load(p), catalog, today) for p in sorted(args.input.glob('*.json'))]
        print(json.dumps(queue(catalog, args.region, args.industry, args.limit, cases, today), ensure_ascii=False, indent=2))
    elif args.command == 'validate':
        cases = [validate(load(p), catalog, today) for p in sorted(args.input.glob('*.json'))]
        require(bool(cases), 'no evidence cases')
        print(f'Validated {len(cases)} cases')
    else:
        print(f'Built {len(build(args.input, args.output, catalog, today))} cases')


if __name__ == '__main__':
    main()

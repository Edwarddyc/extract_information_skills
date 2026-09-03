# Source Policy

## Portfolio Size

Maintain 50-70 standing sources after calibration:

| Tier | Target | Scan behavior |
|---|---:|---|
| `core` | 12-16 | Check every weekly run |
| `specialist` | 24-32 | Check when its axis or topic is active |
| `weak-signal` | 12-20 | Sample for discovery; verify elsewhere |
| `trial` | up to 10 | Evaluate for four runs, then promote or pause |

The starter registry is a seed set, not an obligation to reach the target immediately.

Sources listed in `data/priority-watchlist.csv` are mandatory weekly checks regardless of tier. Tier controls broad scan order; the priority watchlist controls guaranteed coverage.

## Source Order

Prefer the nearest available artifact:

1. Paper, code, documentation, release notes, benchmark data, standards text, or official changelog.
2. First-party research or engineering explanation.
3. Author talk, project issue, or maintainer discussion.
4. Independent technical analysis with reproducible evidence.
5. Community discussion, social post, or aggregator, used primarily for discovery.

Do not equate first-party with unbiased. It improves provenance, not truth. For consequential performance or adoption claims, look for independent evidence.

## No-Key Access Methods

Preferred methods:

- public RSS or Atom feeds;
- public web pages found through normal search;
- GitHub repository, release, issue, discussion, and raw-file pages;
- arXiv, OpenReview, ACL Anthology, PMLR, and conference proceedings pages;
- public documentation and changelogs;
- public YouTube pages or transcripts when accessible without login.

Allowed automated fallback: a public, documented endpoint that works without a key, but the Skill must still produce a structured failure state if it disappears. Avoid unofficial mirrors when an official page exists. Do not introduce a human collection step.

Repository and documentation URLs can move. Validators and source checks should compare normalized official hosts and maintain narrow aliases for known renames instead of assuming one historical path forever. Known MCP specification aliases include `github.com/modelcontextprotocol/specification`, `github.com/modelcontextprotocol/modelcontextprotocol`, and `modelcontextprotocol.io`.

Excluded as required dependencies:

- commercial search/news APIs;
- GitHub personal access tokens;
- X, Reddit, or newsletter APIs;
- paid academic databases;
- browser sessions that require the user's private login.

## Registry Schema

`data/source-registry.csv` fields:

- `id`: stable lowercase identifier.
- `name`: human-readable source name.
- `url`: feed or public index URL.
- `access`: `rss`, `atom`, `page`, or `search`.
- `tier`: `core`, `specialist`, `weak-signal`, `trial`, or `paused`.
- `axes`: pipe-separated `framework`, `evaluation`, `evolution`, `product`.
- `cadence`: `weekly`, `biweekly`, `monthly`, or `event`.
- `trust`: integer 1-5 for provenance and demonstrated reliability.
- `noise`: integer 1-5; 5 means very noisy.
- `query_hint`: optional search terms or filtering hint.
- `reason`: concise retention rationale.

## Promotion and Removal

Track yield during source reviews:

- `useful yield`: retained items divided by reviewed items.
- `unique yield`: retained items not found earlier from a stronger source.
- `depth yield`: items promoted to deep read or long-term knowledge.

Promote a trial source after at least three useful items across four runs. Downgrade or pause a source after eight active runs with no retained item, unless it covers a rare but critical event class. Remove duplicates that repeatedly point to the same upstream artifact.

Do not optimize only for yield. Keep a few low-frequency official sources whose silence or occasional protocol change is strategically important.

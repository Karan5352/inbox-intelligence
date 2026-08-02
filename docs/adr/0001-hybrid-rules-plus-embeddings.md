# ADR 0001: Rules first, then a local model

- Status: Accepted
- Date: 2026-08

## Context

Email has to be sorted into about a dozen categories. Two obvious approaches each
fall short on their own:

- Rules are precise and easy to explain, but brittle. They only catch the cases
  someone thought to write down, so they cover the obvious mail and miss the rest
  (measured around 69% on the synthetic set).
- A model generalises but is opaque, and it spends effort on mail a one-line rule
  already handles with certainty (a known carrier, an unsubscribe header).

## Decision

Run rules first. If a rule is confident enough (the threshold is configurable),
use it. Otherwise hand the email to the local embedding classifier. Every result
records where it came from (rule or model) and a short reason.

## Consequences

- On the synthetic benchmark (single-label, 12-class, 5-seed mean) with MiniLM:
  rules alone reach ~72%, the model alone ~91%, and the hybrid ~92%. The rules edge
  the model by correctly catching cases it scatters (an unambiguous "mentioned you"
  is social, a known bank is finance) while the model handles the rest.
- The margin is small on purpose: the rules only override the model when they are
  genuinely precise, so they add a point or two without dragging down the model's
  coverage. The zero-dependency fallback embedder scores a little differently on the
  synthetic set; `RESULTS.md` records which embedder produced its numbers.
- Real-world accuracy is unmeasured (no ground truth on a live inbox); the value on
  real mail comes from fixing concrete failure modes, not the benchmark number.
- Getting the domain matching right (label-boundary match, so "x.com" does not match
  "dropbox.com") mattered: a loose match was misfiling mail and pulling the hybrid
  below the model.
- The UI can always say why an email landed where it did, which is the durable
  reason to keep the rules regardless of embedder.
- The confidence threshold is a real knob, tuned with the benchmark, not by guessing.

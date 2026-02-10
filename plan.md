# Compound Engineering Implementation Plan for Ignition

## Problem Statement
Traditional development practices lead to technical debt accumulation. Compound engineering emphasizes thorough planning and review to reduce technical debt. We need to enhance the ignition framework to support compound engineering principles and self-improvement mechanisms.

## Proposed Approach
Integrate compound engineering practices directly into the ignition pipeline by:
1. Adding validation gates that enforce planning quality
2. Implementing review stages that catch technical debt before it compounds
3. Creating self-improvement feedback loops that learn from past iterations
4. Building metrics and reporting to track technical debt trends

## Workplan

### Phase 1: Core Compound Engineering Concepts ✅ DONE
- [x] Create `compound.py` module for compound engineering primitives
- [x] Define TechnicalDebt model (Pydantic) to track debt items
- [x] Define PlanningQuality model to measure plan thoroughness
- [x] Define ReviewGate model for validation checkpoints
- [x] Add compound engineering config parameters to `config.py`

### Phase 2: Planning Enhancement Stage ✅ DONE
- [x] Create `stages/planning.py` - new stage after decomposition
- [x] Implement plan quality validator (checks for gaps, ambiguities, dependencies)
- [x] Add "Definition of Done" checker for each task
- [x] Generate planning quality report (score tasks on completeness)
- [x] Integrate planning stage into runner.py pipeline

### Phase 3: Review Gate Implementation ✅ DONE
- [x] Create `stages/review.py` - validation stage before committing
- [x] Implement technical debt detector (code smells, TODOs, hardcoded values)
- [x] Add dependency analyzer (detects tight coupling, circular deps)
- [x] Create review checklist generator per task type
- [x] Add review gate to Ralph loop template

### Phase 4: Self-Improvement Mechanisms ✅ DONE
- [x] Create `stages/reflection.py` - post-iteration learning stage
- [x] Implement iteration analyzer (what worked, what didn't)
- [x] Add pattern library builder (successful patterns get recorded)
- [x] Create anti-pattern detector (failed patterns get flagged)
- [x] Build improvement suggestions generator
- [x] Add retrospective output to track learnings

### Phase 5: Metrics and Reporting ✅ DONE
- [x] Create `metrics.py` - compound engineering metrics
- [x] Track technical debt score per iteration
- [x] Track plan quality trend over iterations
- [x] Track review gate pass/fail rates
- [x] Generate compound engineering metrics report (markdown)
- [x] Add self-improvement composite score

### Phase 6: Ralph Loop Integration ✅ DONE
- [x] Update `ralph.sh` to include planning step (pre-iteration)
- [x] Update `ralph.sh` to include review step (post-iteration)
- [x] Update `ralph.sh` to include reflection step (post-sprint)
- [x] Update `ralph.ps1` with same enhancements
- [x] Add compound engineering mode flag (--compound)

### Phase 7: Testing ✅ DONE
- [x] Add `tests/test_compound.py` - core models tests (19 tests)
- [x] Add `tests/test_planning.py` - planning stage tests (6 tests)
- [x] Add `tests/test_review.py` - review gate tests (4 tests)
- [x] Add `tests/test_reflection.py` - reflection stage tests (6 tests)
- [x] Add `tests/test_metrics.py` - metrics calculation tests (6 tests)
- [x] Run full test suite — 165/165 passing, zero regressions

### Phase 8: Templates and Documentation
- [ ] Create `templates/compound/planning-template.md.j2`
- [ ] Create `templates/compound/review-checklist.md.j2`
- [ ] Create `templates/compound/reflection-report.md.j2`
- [ ] Update README.md with compound engineering section
- [ ] Create examples/compound/ with sample use case

## Key Design Decisions

### Pipeline Architecture (Compound Mode)
The pipeline expands from 7 to 10 stages when `--compound` is enabled:

```
Input → Parse → Decompose → PRD → [Planning Gate] → Scaffold → Ralph → [Review Gate] → Verify → [Reflection]
  1       2        3          4         5              6          7          8             9          10
```

The 80/20 split is achieved: stages 5, 8, and 10 (planning, review, reflection)
handle the compound engineering work, while stage 7 (Ralph) is the execution.

### Recursive Self-Improvement Architecture

```
Sprint N                          Sprint N+1
┌──────────────────┐              ┌──────────────────┐
│  Planning Gate   │◄────────────┤  Feed-Forward     │
│  (quality score) │              │  Context Loaded   │
├──────────────────┤              ├──────────────────┤
│  Ralph Loop      │              │  Ralph Loop       │
│  (execution)     │              │  (improved plans) │
├──────────────────┤              ├──────────────────┤
│  Review Gate     │              │  Review Gate      │
│  (debt tracking) │              │  (fewer issues)   │
├──────────────────┤              ├──────────────────┤
│  Reflection      │──────────►  │  Reflection       │
│  - patterns      │  persist    │  - patterns grow  │
│  - anti-patterns │  via .json  │  - debt decreases │
│  - improvements  │             │  - velocity up    │
└──────────────────┘              └──────────────────┘
```

How it works:
1. `CompoundState` persists in `.ignition/compound-state.json`
2. At sprint start, `begin_sprint()` builds feed-forward context from last retro
3. Feed-forward context is injected into the Planning stage's LLM prompt
4. The planning LLM sees: past patterns, anti-patterns, improvements, debt count
5. This makes planning quality improve with each sprint (measurable via trends)
6. At sprint end, `end_sprint()` records retrospective and updates trends
7. The pattern library grows monotonically — knowledge compounds

### Planning Quality Metrics
- **Completeness**: Are all aspects of the task defined? (acceptance criteria, test plan, dependencies)
- **Clarity**: Is the task description unambiguous?
- **Testability**: Can success be objectively verified?
- **Scope**: Is the task appropriately bounded?
- **Score**: 0-100 per task, aggregate to PRD level

### Review Gates
- **Pre-commit gate**: Runs before each Ralph iteration commit
- **Checks**: Code quality, test coverage, dependency analysis, technical debt scan
- **Threshold**: Configurable pass/fail thresholds
- **Output**: Review report with findings and recommendations

### Self-Improvement Loop
- **After each iteration**: Analyze what patterns led to success/failure
- **Pattern library**: Store successful approaches (e.g., "breaking down UI tasks into component + logic + test")
- **Anti-patterns**: Flag problematic approaches (e.g., "skipping integration tests led to bugs")
- **Feedback**: Inject learnings into next iteration's planning

### Integration Points
- **Stage 5 (Planning)**: After decomposition, before scaffold — validates and enriches PRD
- **Stage 8 (Review)**: After Ralph iteration, before verify — catches debt
- **Stage 10 (Reflection)**: After verify, end of pipeline — extracts learnings

### Persistence
- `.ignition/compound-state.json` — full compound state across sprints
- `.ignition/reviews/review-iter-N.json` — per-iteration review reports
- `.ignition/retrospectives/sprint-N.json` — per-sprint retrospectives
- `.ignition/feed-forward.md` — human-readable context for next sprint
- `planning-report.json` — latest planning quality report
- `compound-metrics.md` — latest metrics dashboard

## Success Criteria
1. Planning quality score increases over iterations (evidence of learning)
2. Technical debt score decreases or remains stable (not accumulating)
3. Review gates catch issues before they compound
4. Pattern library grows with successful approaches
5. No regression in existing ignition functionality

## Notes
- Compound engineering mode is opt-in (`--compound` flag) — backward compatible
- Self-improvement data persists in `.ignition/` directory across runs
- Tutorial mode explains compound engineering concepts when `--tutorial` is also set
- Metrics are actionable: self-improvement score tracks 5 signals
- Pattern library grows monotonically — knowledge is never lost
- Feed-forward mechanism makes the system recursively self-improving between sprints

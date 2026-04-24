# Product Requirements Document (PRD): sloan-sim

**Version:** 0.2.0  
**Status:** Specification  
**Owner**: jpawebb

---

## 1. Executive Summary
Student Loan Simulator (`sloan-sim`) is an open-source, UK-specific student-loan repayment simulator. Gifen a borower's salary, expected salary growth, and one ormore SLC loan balances (across any combination of Plans 1, 2, 4, 5, and Postgraduate (3)), it projects month-by-month interest accruel, income-contingent repayments, and the date the loan is either repaid or written off. 

Unline HMRC's "find out how much you'll repay" tool -- which only reports the next payslip deduction, `sloan-sim` models the **full lifetime** of the loan under user-defined salary trajectories, and lets users compare scenarios (e.g. "minimum repayment" vs. "voluntary overpayment", "Plan 2 only" vs. "Plan 2 + PG"). It is a **library first**, with a CLI and a Streamlit dashboard on top.

**Non-goals**: Tax/NI calculation beyond what is required for repayment; US loans; advice or regulated financial recommendations.

---

## 2. Target Users
| Personal | Need |
| --- | --- |
| **Future Graduates** | Assess the long-term implications of each loan before taking it out. |
| **Recent UK Graduate** | Understand whether overpaying is wothwhile vs. letting the loan be written off at the end of the plan term. |
| **Mid-career professionals with multiple plans** (e.g. Plan 2 + Postgraduate) | See how repayments are split across plans and when each clears. |
| **Career-changer/ sabbatical planner** | Model salary dips, gaps, and recoveries on payoff date. |
| **Personal-finance hobbyist / FIRE community** | Run scenarios, export schedules to CSV, plug results into spreadsheets. |
| **Developer / contributor** | A clean, well-tested Python engine they can import and extend. |


## 3. Scope

### 3.1 In scope (MVP → v1.0)
- Plans 1, 2, 4, 5, and Postgraduate (Plan 3) -- interest rules, thresholds, repayment percentages, and write-off terms.
- Deterministic monthly simulation with annual salary growth.
- Multiple concurrent loans per user, with HMRC-correct repayment ordering.
- CLI and Streamlit dashboard.
- CSV/JSON export of the full amortisation schedule.

### Out of scope (MVP)
- Real-time rate-scraping from gov.uk (rates are versioned in-repo, see §6.4).
- Self-Assessment/ Pay-As-You-Earn reconcilliation differences.
- Salary sacrifice, pension contributions, or benefits-in-kind affecting "income for student loan purposes" -- *deferred to v1.1*.
- Mortgage-style refinancing or private loans.
- Mobile app.

---

## 4. Functional Requirements

### 4.1 Core Simulation Engine (`src/core/`)
**FR-1. Loan Modelling**. A `LoanProduct` defines plan-level constants (earning threshold, repayment rate, write-off term, interest calculation window, interest application window, intrest rules). A `UsersLoanProduct` attached a balance, a start date (or `years_since_graduate`), and a reference to the borrower.

**FR-2. Effective Interest Rate**. Per plan, must implenent:
- **Plan 1 & Plan 4**: `min(RPI + 3%, PMR cap)`.
- **Plan 2**: Sliding scale between RPI (≤ lower threshold) and RPI + 3% (≥ upper threshold), capped by the Prevailing Market Rate (currently 6%).
- **Plan 3 / Postgraduate**: `min(RPI + 3%, PMR cap)`.
- **Plan 5**: `min(RPI, PMR cap)`
- Unknown `loan_id` must raise `ValueError` (today it silently returns `None`).

**FR-3. Repayment Calculation**. For each pay period, computethe borrower's repayment as: `max(0, (annual_income - plan_threshold) * plan_rate) / 12` if monthly where `plan_rate` is 9% (Plans 1, 2, 4, 5) or 6% (Postgraduate).

**FR-4. Multi-Loan Ordering (HMRC rules)**.
- Plan 1/2/4/5 loans share a single 9% deduction; if a borrower has more than one undergraduate plan, repayments are allocated to the lowest-numbered plan first.
- Postgraduate loans take an **additional** 6% deduction. calculated independently against the PG threshold.

**FR-5. Monthly Simulation Loop**. For each month from `start_date` until all loans are repaid or written off:
1. Apply interest for the period (respecting `InterestCalculationWindow` and `InterestApplicationWindow`).
2. Compute repayment from current annualised salary.
3. Allocate repayment across loans per FR-4.
4. Decrement balance; record a `MonthlyLedgerEntry`.
5. On each anniversary, apply the user's estimated salary growth rate.
6. On reaching `payment_term_years` for a given loan, write off the remaining balance and stop accruing on that loan.

**FR-6. Salary Growth Model**. Support:
- Constant annual % growth (MVP).
- Piecewise / per-year overrides (e.g. `[0.05, 0.05, 0.10, 0.03, ...]`).
- *(v1.1)* Stochastic Monte-Carlo growth: sample from a user-defined normal/log-normal distribution; return percentail banks (P10, P50, P90) on payoff date and total interest paid.

**FR-7. Outputs**. A `SimulationResult` containing:
- Per-loan amortisation table (date, opening balance, interest accrued, repayment applied, closing balance).
- Aggregate metrics: total interest paid, total repaid, payoff date per loan and overall (plus payoff date per loan and overall if there was no `payment_term_years`), % of original principle recovered by SLC.

**FR-8. Voluntary Overpayments**. Optional one-off or recurring extra payments, allocated by user-chosen strategy (`highest_rate_first`, `shortest_term_first`, `pro_rata`).


### 4.2 Versioned rates (`resources/rates,yml`)
All rate-like constants (RPI, BoE base, plan thresholds, repayment rates, PMR cap, write-off terms) move out of `loan_engine.py` into a YAML file keyed by **UK tax year** (e.g. `2025-26`). The engine selects the row matching the simulation date. This is required for:
- Backtesting against a real borrowers history.
- Reproduceability when SLC publishes new figures.
- Tests that pin behaviour to a specific tax year.

### 4.3 CLI (`sloan-sim`)
```bash
sloan-sim simulate \
    --salary 35000 --growth 0.04 \
    --loan plan_2:45000:2021-09 \
    --loan postgraduate:12000:2024-09 \
    --overpay 100/month \
    --until-paid \
    --out schedule.csv
```
- Pretty-printed summary to stdout (payoff date, total interest, written-off amount).
- `--out` accepts `.csv` or `.json`.
- `--scenario` flag to load a YAML scenario file for reproduceability.

### 4.4 Dashboard (Streamlit)
- Inputs: salary (number), salary growth (slider 0-100%), one or more loans (plan + balance + startstate), optional overpayment.
- Outputs:
    - **"Freedom Date"** card -- month/year all loans clear (or "written off" with date).
    - **% paid off per loan and total**.
    - **% of term elapsed/ remaining**.
    - Stacked-area chart of balance over time per-plan.
    - Line chart of cumulative interest vs. cumulative principle repaid.
    - Scenario A vs. Scenario B side-by-side comparison.
- "Download schedule" button exports the underlying ledger as CSV.


### 4.5 Privacy & Data
- 100% local computation. No network calls at runtime. No telemetry.

## 5. Non-Functional Requirements

| Area | Requirement |
| :--- | :--- |
| **Correctness** | ≥ 95% line coverage on `src/core/`. Property-based tests (Hypothesis) for invariants: balance never negative, write-off honoured at term, monotonic decay under zero growth + ≥ minimum repayment. |
| **Performance** | A 30-year monthly simulation completes in < 200 ms on a laptop. 10000 run Monte Carlo completes in < 10 s. |
| **Portability** | Pure Python, no compliled deps in MVP. Runs on macOS, Linux, Windows, Python 3.10+. |
| **Packaging** | Installable via `pip install sloan-sim` and `uv add sloan-sim`. CLI exposed as a project script.
| **Quality gates** | CI runs `pytest`, `ruff`, `mypy --strict` on `src/core/`, and coverage report on every push and PR.
| **Docs** | README quickstart, `docs/` with engine reference and a worked example per plan. Docstrings on every public class/method.
| **Licence** | MIT? |

---

## 6. Archtecture & Tech Stack

### 6.1 Layout
```
src/
    core/
        rates.py                # Loads & validates resources/rates.yml
        plans.py                # LoanPlan strategy classes (one per plan, registered via enum)
        engine.py               # Simulation loop, ledger, SimulationResult
        models.py               # User, UserLoanProduct, MonthlyLedgerEntry (dataclasses)
    cli/
        __main__.py             # Typer-based CLI
    app/
        streamlit_app.py        # Dashboard
resources/
    rates.yml                   # Versioned by tax year
tests/
    core/                       # Unit + property tests
    cli/
    fixtures/                   # Know-good scenarios
```


### 6.2 Key Design Choices
- **Strategy Pattern, not if/elif**, for plan-specific interest and repayment rules, each plan is a class registered against an enum value.
- **Dataclasses** for all value objects; engine returns immutable `SimulationResult`.
- **Pure Functions** for inner loop -- no I/O, no globals, engine remains trivailly testable and Monte-Carlo friendly.
- **No Mutable Module-Level Rate Constants**; rates are passed in, or resolved by date.


### 6.3 Tech Stack
| Layer | Choice |
| :--- | :--- |
| Language | Python 3.10+ |
| Package / Environment Management | `uv` |
| CLI | `typer` |
| Dashboard | `streamlit` + `altair` |  
| Data | `pydantic` for input validation, `pyyaml` for rates | 
| Testing | `pytest`, `pytest-cov`, `hypothesis` | 
| Lint / format / types | `ruff`, `black`, `mypy` |
| CI | GitHub Actions |


### 6.4 Rate Data Governance
- `resources/rates.yml` is the single source of truth.
    - In future these will be pulled from gov.uk systematically.
- updates land via PR with a citation to the gov.uk SLC source in the commit message.
- A `tests/test_rates.py` snapshot test guards against accidental edits to historical rows.

---

## 7. Roadmap

### v0.2 - Engine completion (next)
- [x] Fix `VariableInterestRate.__init__(self)` and remove if not used.
- [ ] Raise on unknown `loan_id` in `effective_interest_rate`.
- [ ] Add Plan 4, Plan 5, and Postgraduate branches with tests. 
- [ ] Move constants into `resources/rates.yml` keyed by tax year.
- [ ] Implement monthly simulation loop with salary growth (FR-5, FR-6 constant case).

### v0.3 - Multi-loan + overpayments
- [ ] HMRC repayment ordering across multiple plans (FR-4).
- [ ] Voluntary overpayments with allocation strategies (FR-8).
- [ ] CSV/JSON export.

### v0.4 - CLI & docs
- [ ] `typer` CLI per §4.3.
- [ ] README rewrit, `docs/` site, worked examples per plan.
- [ ] Coverage badge, ruff/mypy in CI.

### v1.0 - Dashboard
- [ ] Streamlit app per §4.4, including scenario A/B comparison.
- [ ] Published to PyPI.

### v1.1 - Stochastic + advanced
- [ ] Monte-Carlo salary growth with P10/P50/P90 fan chart
- [ ] Property-based tests via Hypothesis
- [ ] Pension / salary-sacrifice adjustments to "income for student loan purposes".

---

## 8. Success Metrics
| Metric | Target (12 months post-v1.0) |
| :--- | :--- |
| Engine accuracy vs. SLC published numbers | ≤ £1 difference per year of simulation |
| Test coverage `src/core/` | ≥ 95%


## 9. Risks & Mitigations
| Risk | Liklihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Misinterpreting SLC interest/ threshold rules | Medium | High | Cite gov.uk per rate row; cross-check against SLC's own example calculation in tests. | 
| Rates change mid-tax-year | Medium | Medium | Date-keyed `rates.yml` supports mid-year transitions. | 
| Floating point drift over 30-year simulations | Low | Medium | Use `Decimal` for monetary amounts in the ledger; only cast to `float` for charting. | 
| Scope creep into general personal-finance app | Medium | Medium | Out-of-scope list in §3.2; PRs touching tax/pension require issue first. |
| Maintainer bandwidth | High | Medium | Keep core engine deliberately small; defer features to v1.1+ |


## 10. Open Questions
1. Should Scotland's Plan 4 thresholds and write-off terms be pinned per academic year of borrowing, or per current tax uear? (Affects FR-2 and `rates.yml` schema.)
2. For multi-plan borrowers below the lower threshold, do we still need to recorda. £0 payslip row in the ledger, or skip it? (Affects ledger size on long simulations. I believe it should record £0.)
3. Do we want a "what if I change plan rules" sandbox mode (override `rates.yml` from the CLI), or keep rates immutable per run? (I believe keep rates immutable.)
4. Officially choose a license.
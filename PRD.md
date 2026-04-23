# Product Requirements Document (PRD): Lumen Loan

**Version:** 1.0  
**Status:** Draft / Specification  
**Platform:** iOS (SwiftUI)

---

## 1. Executive Summary
Lumen Loan is a high-end financial forecasting tool that allows users to manually input student loan data and simulate repayment timelines based on custom salary growth projections. Unlike traditional banking apps, it focuses on **user-driven "What-If" scenarios** without requiring bank account linking or sensitive data sharing.

## 2. Target Audience
* **Recent Graduates:** Looking to understand how their first few raises will impact their debt.
* **High-Earners:** Professionals planning aggressive repayment strategies.
* **Privacy-Conscious Users:** Individuals who want financial insights without the security risks of third-party data aggregators.

## 3. Functional Requirements

### 3.1 Core Simulation Engine
* **Loan Inputs:** Manual entry for Principal Balance, Annual Interest Rate, and Current Monthly Payment.
* **Salary Inputs:** Starting Annual Salary and a **Custom Annual Percentage Change (Growth Rate)**.
* **Math Logic:** The engine must calculate monthly interest accrual, principal reduction, and the "Total Interest Paid" over the life of the loan.
* **Scenario Comparison:** Ability to toggle between at least two growth rates (e.g., 3% vs. 5%) to see the difference in the "Freedom Date."

### 3.2 Visualization & UI
* **Dynamic Dashboard:** Real-time updates. When a slider moves, the graph must animate instantly.
* **The "Freedom Clock":** A prominent display of the month and year the loan reaches $0.
* **Amortization Chart:** A high-fidelity line chart showing the balance declining over time.

### 3.3 Data & Privacy
* **No Third-Party Auth:** No Plaid, no bank logins, no SSN required.
* **Local Persistence:** User data is stored locally on the device using **SwiftData**. No cloud database is required for MVP.

---

## 4. User Experience (UX) & Design

### 4.1 The "Sleek" Aesthetic
* **Design Language:** Dark Mode first. Use of "Glassmorphism" (ultra-thin materials) and subtle gradients.
* **Interactive Haptics:** Use of `UIImpactFeedbackGenerator` when sliders hit milestones (e.g., shaving off 1 year of debt).
* **Typography:** Clean, sans-serif fonts (e.g., SF Pro Display) with high contrast for financial figures.

---

## 5. Technical Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Swift 6.0+ |
| **Framework** | SwiftUI |
| **Charts** | Swift Charts (Native) |
| **Data Storage** | SwiftData (Local-only) |
| **Architecture** | MVVM-Service (Feature-based) |

---

## 6. Roadmap & Monetization

### Phase 1: MVP (Minimum Viable Product)
* Manual loan and salary entry.
* Single-line amortization chart.
* Single salary growth slider.

### Phase 2: Premium Features (Monetization)
* **Scenario Vault:** Save and compare multiple "Life Paths" (e.g., "Stay in Public Service" vs. "Private Sector").
* **The "Windfall" Planner:** One-time manual entries for bonuses or tax refunds.
* **PDF Export:** Professional "Financial Freedom Report" generation.

### Phase 3: Affiliate Expansion
* **Contextual Refinancing:** Recommendations for refinancing partners based on user-inputted interest rates (Lead Gen).

---

## 7. Success Metrics
* **User Retention:** Frequency of users returning to "tweak" their salary growth as they get raises.
* **Conversion Rate:** Percentage of users upgrading to "Premium" to save multiple scenarios.
* **Privacy Score:** 100% Zero-Data-Collection on the App Store Privacy Label.

---

## 8. Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Math Inaccuracy** | Implement 100% Unit Test coverage for the `LoanEngine`. |
| **User Entry Fatigue** | Provide "Quick Start" templates for common loan types (Stafford, PLUS, etc.). |
| **Perceived Value** | Focus on the "Sleek" UI and "What-If" dopamine hits to ensure the app feels like a tool, not a calculator. |

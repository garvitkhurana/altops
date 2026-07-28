"""Extraction schemas + the arithmetic identities that must hold for each."""

CURRENCIES = ["USD", "EUR", "GBP", "CHF", "JPY", "CAD", "AUD"]

SCHEMAS = {
    "capital_call": {
        "description": "A notice from a GP requiring the LP to contribute capital. "
                       "May be titled Capital Call, Drawdown Notice, Funding "
                       "Notice, Notice of Capital Contribution, or similar.",
        "fields": {
            "fund_name": "Full legal name of the fund/partnership",
            "gp_manager": "Name of the general partner or management company",
            "notice_date": "Date the notice was issued (ISO YYYY-MM-DD)",
            "due_date": "Date funds must be received (ISO YYYY-MM-DD)",
            "call_number": "Sequential number of this call (integer)",
            "amount": "Total amount called from this LP (number, no symbols)",
            "currency": "ISO currency code",
            "commitment": "LP's total commitment to the fund",
            "cumulative_called": "Contributions to date including this call",
            "unfunded_commitment": "Remaining undrawn commitment",
            "purpose_investments": "Portion for portfolio investments",
            "purpose_management_fee": "Portion for management fees",
            "purpose_expenses": "Portion for partnership expenses",
        },
        # (label, expression, tolerance) -- evaluated against extracted fields
        "identities": [
            ("purpose components sum to call amount",
             "purpose_investments + purpose_management_fee + purpose_expenses == amount",
             0.02),
            ("unfunded = commitment - cumulative called",
             "commitment - cumulative_called == unfunded_commitment", 0.02),
            ("call amount does not exceed unfunded commitment",
             "amount <= unfunded_commitment + amount", 0.02),
        ],
        "date_order": [("notice_date", "due_date")],
    },
    "distribution": {
        "description": "A notice that the GP is distributing cash to the LP.",
        "fields": {
            "fund_name": "Full legal name of the fund/partnership",
            "gp_manager": "Name of the general partner or management company",
            "notice_date": "Date the notice was issued (ISO YYYY-MM-DD)",
            "payment_date": "Date cash is/was paid (ISO YYYY-MM-DD)",
            "distribution_number": "Sequential number of this distribution",
            "amount": "Total distribution to this LP",
            "currency": "ISO currency code",
            "return_of_capital": "Portion characterized as return of capital",
            "realized_gain": "Portion characterized as realized gain",
            "investment_income": "Portion characterized as investment income",
            "recallable_amount": "Portion subject to recall by the GP",
        },
        "identities": [
            ("components sum to distribution amount",
             "return_of_capital + realized_gain + investment_income == amount",
             0.02),
            ("recallable does not exceed return of capital",
             "recallable_amount <= return_of_capital", 0.02),
        ],
        "date_order": [("notice_date", "payment_date")],
    },
    "capital_account_statement": {
        "description": "A periodic statement of the LP's capital account roll-forward.",
        "fields": {
            "fund_name": "Full legal name of the fund/partnership",
            "gp_manager": "Name of the general partner or management company",
            "period_end": "Statement as-of date (ISO YYYY-MM-DD)",
            "currency": "ISO currency code",
            "beginning_nav": "Beginning capital balance",
            "contributions": "Contributions during the period (positive)",
            "distributions": "Distributions during the period (negative)",
            "realized_gain": "Realized gain or loss",
            "unrealized_change": "Change in unrealized value",
            "management_fee": "Management fee charged (negative)",
            "carried_interest": "Carried interest accrual (negative)",
            "ending_nav": "Ending capital balance",
        },
        "identities": [
            ("capital account roll-forward ties",
             "beginning_nav + contributions + distributions + realized_gain + "
             "unrealized_change + management_fee + carried_interest == ending_nav",
             0.05),
        ],
        "date_order": [],
    },
}

# Fields where a wrong value moves money or misses a deadline. These get
# a stricter confidence bar before they are allowed to post automatically.
CRITICAL_FIELDS = {
    "capital_call": ["amount", "due_date", "fund_name", "currency"],
    "distribution": ["amount", "payment_date", "fund_name", "currency"],
    "capital_account_statement": ["ending_nav", "period_end", "fund_name"],
}

# Personal Expense Tracker

I built this Streamlit dashboard as part of my AI engineering journey. It helps you explore how your monthly take-home pay is split across needs, wants, and savings or extra debt repayment.

## What you can do

- Enter your monthly take-home pay in rupees. Changing it recalculates the budget targets while keeping your current entries.
- Enter amounts for multiple categories at once or add a custom category and assign it to a budget group.
- View total spending, savings and extra debt repayments, and the amount left to allocate. The donut chart shows each group's share of the amounts entered.
- Compare your allocations with the 50/30/20 targets and see suggestions when you go over budget, fall short of your savings target, or record no insurance payments.
- Review the items you entered in the monthly ledger.

## How the budget works

| Group | Share of take-home pay | Examples |
| --- | --- | --- |
| Needs | Aim for 50% or less | Rent, groceries, essential transport, insurance premiums, minimum EMI |
| Wants | Aim for 30% or less | Dining out, delivery, personal and leisure spending |
| Savings & Extra Debt Repayment | Aim for at least 20% | Savings and payments above the minimum loan installment |

The app stores entries as a list of dictionaries and uses dictionaries to map categories and aggregate totals. It uses Python's `Decimal` for money and explicit Python rules for suggestions. Streamlit handles the interface, and Altair renders the donut chart.

## Run locally

Open PowerShell in the project folder and run the following with Python 3.12 installed.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL shown in the terminal.

## Try it with sample data

Set take-home pay to **₹45,000**. Add **₹24,000** for Rent & Utilities, **₹10,000** for Dining Out & Delivery, and **₹5,000** for Savings. The app should show **₹34,000 spent**, **₹5,000 saved**, and **₹6,000 left to allocate**. Needs should be **₹1,500 over** the 50% target, and savings should be **₹4,000 short** of the 20% target.

## Session storage

Entries and custom categories are stored for the current browser session. Refreshing the page clears both.

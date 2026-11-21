# Add your budget logic here.
from base64 import b64encode
from decimal import Decimal, InvalidOperation
from pathlib import Path

import altair as alt
import streamlit as st


DEFAULT_CATEGORY_GROUPS = {
    "Rent & Utilities": "Needs",
    "Groceries": "Needs",
    "Essential Transport": "Needs",
    "Health Insurance": "Needs",
    "Term Insurance": "Needs",
    "Minimum EMI": "Needs",
    "Dining Out & Delivery": "Wants",
    "Personal & Leisure": "Wants",
    "Savings": "Savings & Extra Debt Repayment",
    "Extra Debt Repayment": "Savings & Extra Debt Repayment",
}

TARGETS = {
    "Needs": Decimal("0.50"),
    "Wants": Decimal("0.30"),
    "Savings & Extra Debt Repayment": Decimal("0.20"),
}

GROUP_COLORS = {
    "Needs": "#7C8CFF",
    "Wants": "#FFAA66",
    "Savings & Extra Debt Repayment": "#39D9BC",
}

ZERO = Decimal("0.00")
PAISE = Decimal("0.01")


def rupees(amount):
    return f"₹{amount:,.2f}"


def read_amount(text, *, allow_zero=False):
    try:
        amount = Decimal(text.strip())
        if not amount.is_finite() or amount < ZERO:
            return None
        if amount == ZERO and not allow_zero:
            return None
        rounded = amount.quantize(PAISE)
        if amount != rounded:
            return None
    except InvalidOperation:
        return None
    return ZERO if rounded == ZERO else rounded


def calculate_totals(entries, category_groups):
    category_totals = dict.fromkeys(category_groups, ZERO)
    group_totals = dict.fromkeys(TARGETS, ZERO)

    for entry in entries:
        category = entry["category"]
        amount = entry["amount"]
        category_totals[category] += amount
        group_totals[category_groups[category]] += amount

    return category_totals, group_totals


def largest_category(group, category_totals, category_groups):
    categories = [
        category
        for category, budget_group in category_groups.items()
        if budget_group == group
    ]
    return max(categories, key=category_totals.get)


def show_insights(salary, category_totals, group_totals, category_groups):
    st.subheader("What your numbers say")

    allocated = sum(group_totals.values(), ZERO)
    remaining = salary - allocated

    if remaining < ZERO:
        message = f"You’ve allocated {rupees(-remaining)} more than your take-home pay."
        if group_totals["Wants"] > ZERO:
            category = largest_category("Wants", category_totals, category_groups)
            message += (
                f" Start by reviewing {category}, your largest Wants category "
                f"at {rupees(category_totals[category])}."
            )
        st.error(message)

    for group in ("Needs", "Wants"):
        excess = group_totals[group] - salary * TARGETS[group]
        if excess > ZERO:
            category = largest_category(group, category_totals, category_groups)
            st.warning(
                f"{group} are {rupees(excess)} above the "
                f"{TARGETS[group]:.0%} limit. Review {category}, "
                f"your largest category in this group "
                f"at {rupees(category_totals[category])}."
            )

    savings_group = "Savings & Extra Debt Repayment"
    savings_gap = salary * TARGETS[savings_group] - group_totals[savings_group]

    if savings_gap > ZERO:
        message = f"You’re {rupees(savings_gap)} short of your 20% savings target."
        if remaining > ZERO:
            contribution = min(savings_gap, remaining)
            message += (
                f" You have {rupees(remaining)} left to allocate. "
                f"Consider putting {rupees(contribution)} toward savings "
                "or extra debt repayment."
            )
        else:
            message += " Review your current allocations to see what you can free up."
        st.info(message)
    else:
        st.success("You’ve reached your 20% savings and extra debt repayment target.")

    for category in ("Health Insurance", "Term Insurance"):
        if category_totals.get(category, ZERO) == ZERO:
            st.info(
                f"No {category.lower()} payment is recorded this month. "
                "Check your existing coverage and when your next premium is due."
            )


def show_chart(group_totals):
    allocated = sum(group_totals.values(), ZERO)
    chart_rows = []
    legend_rows = []
    legend_colors = dict(zip(TARGETS, ("violet", "orange", "green")))

    for group, amount in group_totals.items():
        if amount > ZERO:
            share = amount / allocated
            chart_rows.append({
                "group": group,
                "amount": float(amount),
                "share": float(share),
            })
            legend_rows.append(
                f":{legend_colors[group]}[●] **{group}** · {rupees(amount)} · {share:.1%}"
            )

    chart = (
        alt.Chart(alt.Data(values=chart_rows))
        .mark_arc(innerRadius=75, outerRadius=105, cornerRadius=4, padAngle=0.025)
        .encode(
            theta=alt.Theta("amount:Q", stack=True),
            color=alt.Color(
                "group:N",
                scale=alt.Scale(domain=list(GROUP_COLORS), range=list(GROUP_COLORS.values())),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("group:N", title="Budget group"),
                alt.Tooltip("amount:Q", title="Amount (₹)", format=",.2f"),
                alt.Tooltip("share:Q", title="Share of entries", format=".1%"),
            ],
        )
    )

    text_color = "#F3F5FF" if st.context.theme.type == "dark" else "#17213A"
    center = (
        alt.Chart(alt.Data(values=[{"total": rupees(allocated)}]))
        .mark_text(fontSize=20, fontWeight="bold", color=text_color)
        .encode(text="total:N")
    )

    st.subheader("Spending and allocations")
    st.caption("Pie chart percentages are shares of the money you’ve entered.")
    st.altair_chart((chart + center).properties(height=252), width="stretch")
    st.markdown("  \n".join(legend_rows))


@st.cache_data
def background_image_url():
    image = Path(__file__).with_name("finance-background.png")
    if not image.is_file():
        return None
    encoded = b64encode(image.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


st.set_page_config(page_title="Personal Expense Tracker", layout="wide")
background_url = background_image_url()
if background_url:
    is_dark = st.context.theme.type == "dark"
    if is_dark:
        overlay = "rgba(14, 18, 39, 0.42)"
        card_color = "rgba(20, 24, 47, 0.88)"
    else:
        overlay = "rgba(245, 247, 255, 0.9)"
        card_color = "rgba(255, 255, 255, 0.92)"

    st.html(f"""
        <style>
            .stApp {{
                background-image: linear-gradient({overlay}, {overlay}), url("{background_url}");
                background-position: center;
                background-size: cover;
                background-attachment: fixed;
            }}
            .st-key-allocations_card, .st-key-budget_card, .st-key-insights_card {{
                background-color: {card_color};
            }}
        </style>
    """)

st.title("Personal Expense Tracker")
st.caption("Plan your monthly take-home pay with the 50/30/20 rule.")

if "entries" not in st.session_state:
    st.session_state.entries = []

if "category_groups" not in st.session_state:
    st.session_state.category_groups = DEFAULT_CATEGORY_GROUPS.copy()
if "amount_table_version" not in st.session_state:
    st.session_state.amount_table_version = 0

category_groups = st.session_state.category_groups

salary_text = st.text_input(
    "Monthly take-home pay (₹)",
    placeholder="Enter your after-tax income",
    help="Use digits without commas, such as 45000 or 45000.50.",
)
salary = read_amount(salary_text)

dashboard = st.container()
entry_tab, ledger_tab = st.tabs(["Add amounts", "Monthly ledger"])

with entry_tab:
    st.subheader("Categories")
    st.caption("Enter amounts in the table, then select Add amounts. Blank cells are skipped.")

    with st.popover("Add new category"):
        with st.form("add_category", clear_on_submit=True):
            new_name = st.text_input("Category name")
            new_group = st.selectbox("Budget group", list(TARGETS))
            add_category = st.form_submit_button("Add category")

        if add_category:
            new_name = " ".join(new_name.split())
            if not new_name:
                st.error("Enter a category name.")
            elif any(new_name.casefold() == name.casefold() for name in category_groups):
                st.error("That category already exists.")
            else:
                category_groups[new_name] = new_group
                st.toast(f"Added {new_name}.")

    table_rows = [
        {"Category": name, "Budget group": group, "Amount (₹)": ""}
        for name, group in category_groups.items()
    ]

    with st.form("add_amounts"):
        edited_rows = st.data_editor(
            table_rows,
            key=f"amount_table_{st.session_state.amount_table_version}",
            disabled=["Category", "Budget group"],
            hide_index=True,
            height="auto",
            width="stretch",
            alt="Expense categories and amounts",
        )
        submitted = st.form_submit_button("Add amounts")

    if submitted:
        if salary is None:
            st.error("Enter valid monthly take-home pay before adding amounts.")
        else:
            new_entries = []
            invalid_categories = []
            for category, row in zip(category_groups, edited_rows):
                amount_text = row["Amount (₹)"]
                if not amount_text or not amount_text.strip():
                    continue
                amount = read_amount(amount_text, allow_zero=True)
                if amount is None:
                    invalid_categories.append(category)
                else:
                    new_entries.append({"category": category, "amount": amount})

            if invalid_categories:
                st.error(
                    "Enter zero or a positive amount with up to two decimal places for "
                    + ", ".join(invalid_categories)
                    + "."
                )
            elif not new_entries:
                st.info("Enter an amount in at least one category.")
            else:
                st.session_state.entries.extend(new_entries)
                st.session_state.amount_table_version += 1
                st.session_state.saved_amount_count = len(new_entries)
                st.rerun()

    saved_amount_count = st.session_state.pop("saved_amount_count", None)
    if saved_amount_count is not None:
        st.success(f"Added {saved_amount_count} amount(s) to the monthly ledger.")

entries = st.session_state.entries
category_totals, group_totals = calculate_totals(entries, category_groups)

with dashboard:
    if salary is None:
        if salary_text.strip():
            st.warning("Enter take-home pay above zero with up to two decimal places.")
        else:
            st.info("Enter your monthly take-home pay to see your budget targets.")
    else:
        spending = group_totals["Needs"] + group_totals["Wants"]
        savings = group_totals["Savings & Extra Debt Repayment"]
        remaining = salary - spending - savings

        spent_column, saved_column, balance_column = st.columns(3)
        spent_column.metric("Spent", rupees(spending), border=True)
        saved_column.metric("Saved or paid extra", rupees(savings), border=True)
        balance_column.metric("Left to allocate", rupees(remaining), border=True)

        budget_rows = []
        for group, ratio in TARGETS.items():
            target = salary * ratio
            actual = group_totals[group]
            target_label = "Minimum" if group == "Savings & Extra Debt Repayment" else "Limit"
            budget_rows.append({
                "Group": group,
                "Target": f"{ratio:.0%} {target_label.lower()} · {rupees(target)}",
                "Allocated": rupees(actual),
                "Share of pay": f"{actual / salary:.1%}",
            })
        chart_column, insights_column = st.columns([1, 1.25], gap="medium")
        with chart_column:
            with st.container(border=True, key="allocations_card"):
                if any(group_totals.values()):
                    show_chart(group_totals)
                else:
                    st.subheader("Spending and allocations")
                    st.info("Add a positive amount to see your budget split.")
        with insights_column:
            with st.container(border=True, key="budget_card"):
                st.subheader("50/30/20 budget")
                st.dataframe(budget_rows, hide_index=True, alt="50/30/20 budget targets")
            if entries:
                with st.container(border=True, key="insights_card"):
                    show_insights(salary, category_totals, group_totals, category_groups)


with ledger_tab:
    st.subheader("Monthly ledger")
    if entries:
        st.table([
            {
                "Category": entry["category"],
                "Group": category_groups[entry["category"]],
                "Amount": rupees(entry["amount"]),
            }
            for entry in entries
        ])
    else:
        st.write("No entries yet.")

st.divider()
st.caption("This is a demo project as part of my AI engineer journey.")
with st.container(horizontal=True, gap="small"):
    st.link_button(
        "LinkedIn",
        "https://www.linkedin.com/in/praneeth-koushik-sripada-92665a21b/",
        icon=":material/work:",
    )
    st.link_button("GitHub", "https://github.com/praneethk99", icon=":material/code:")
    st.link_button("Medium", "https://medium.com/@praneethk9912", icon=":material/article:")
    st.link_button("Email", "https://mail.google.com/mail/?view=cm&fs=1&to=praneethk9912%40gmail.com", icon=":material/mail:")
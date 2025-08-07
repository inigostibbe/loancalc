import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")

st.title("Welcome to the Loan Calculator App!")
st.markdown("""
This app helps you estimate your student loan repayments over time based on your loan amount, interest rate, and expected salary growth. You can explore different repayment scenarios, compare the impact of extra repayments, and understand the total and net present value (NPV) of your repayments.
""")

advanced = st.checkbox("Advanced Mode")

col1, col2, col3 = st.columns(3)
with col1:
    amount = st.number_input("Student loan amount", value=50000, step=1000)
with col2:
    interest = st.number_input("Loan interest rate" , value = 7.2 , step = 0.1)
with col3:
    salary = st.number_input("Expected starting salary (5% YoY increase)", value = 30000, step = 500)

# Extra inputs for advanced users
if advanced:
    with col1:    
        increase = st.number_input("Average pay increase (%)", value = 5)
    with col2:
        years = st.number_input("Years", value = 30)
    with col3:
        repay_percentage = st.number_input("Repayment percentage (Default = 9%)", min_value = 9.0, max_value = 100.0, step = 0.1, value = 9.0)
else:
    # Default values for non-advanced users
    increase = 5
    years = 30
    repay_percentage = 9.0

# Calc salary
def simulate_salary(salary, increase, years):
    salary_array = np.zeros(years)
    for idx in range(years):
        salary_array[idx] = salary * (1 + increase / 100) ** idx
    return salary_array

salary_array = simulate_salary(salary, increase, years)

# Calc loan repayment and remaining amount

def simulate_repayment(years = 30, amount = 50000, interest = 7.2, rate = 9.0, min_salary=27295):
    repay_array = np.zeros(years)
    amount_array = np.zeros(years)
    amount_remaining = amount

    for idx in range(years):
        if amount_remaining <= 0:
            repay_array[idx] = 0
            amount_array[idx] = 0
            continue

        annual_salary = salary_array[idx]
        annual_repay = max((annual_salary - min_salary) * rate / 100, 0)

        amount_remaining += amount_remaining * (interest / 100)
        actual_payment = min(annual_repay, amount_remaining)
        amount_remaining -= actual_payment

        repay_array[idx] = actual_payment
        amount_array[idx] = amount_remaining

    return repay_array, amount_array

repay_array, amount_array = simulate_repayment(years=years, amount=amount, interest=interest, rate=repay_percentage)


# Display results
col21, col22, col23 = st.columns(3)

with col21:
    st.subheader("Salary (£)")
    st.line_chart(salary_array)
with col22:
    st.subheader("Monthly Repayments (£)")
    st.bar_chart(repay_array/12)
with col23:
    st.subheader("Remaining Loan Balance (£)")
    st.line_chart(amount_array)

total_repayment = np.sum(repay_array)
st.markdown(f"<h1 style='text-align: center;'>Total Repayment over {years} years: £{round(total_repayment)} </h1>", unsafe_allow_html=True)


st.subheader("Should you increase your repayment rate?")

max_extra = st.slider("Extra repayment (%)", 0, 21, 0)   # 0–6 extra → 9–15 total
rates_to_test = np.array([9, 9 + max_extra])            # e.g. [9, 15]

salary_array = simulate_salary(salary, increase, years)

totals, npvs = [], []
discount_rate = 0.02

for rate in rates_to_test:
    repay, _ = simulate_repayment(
        years=years,
        amount=amount,
        interest=interest,
        rate=rate
    )
    totals.append(repay.sum())

    npv = sum(repay[t] / ((1 + discount_rate) ** t) for t in range(years))
    npvs.append(npv)

# unpack for clarity
total_base,  total_high  = totals
npv_base,    npv_high    = npvs

delta_cash = total_high - total_base      # extra you pay in £
delta_npv  = npv_base   - npv_high        # interest you save in £ (today's value)

if max_extra == 0:
    st.info("Slide the **Extra repayment (%)** above 0 % to see the comparison.")
else:
    st.write(f"Base rate (9 %): **£{total_base:,.0f}** total, NPV £{npv_base:,.0f}")
    st.write(f"Higher rate ({9+max_extra} %): **£{total_high:,.0f}** total, NPV £{npv_high:,.0f}")

    if delta_npv > delta_cash:
        st.success(
            f"✅ Paying {9+max_extra} % looks better: "
            f"saves ≈£{delta_npv:,.0f} in today’s money "
            f"for an extra £{delta_cash:,.0f} of nominal cash."
        )
    else:
        st.info(
            f"💡 Stick to 9 %: extra cash up‑front (£{delta_cash:,.0f}) "
            f"outweighs the discounted interest saved (£{delta_npv:,.0f})."
        )


st.markdown(r"""
### Net Present Value (NPV)

**Definition**  
*Net Present Value* is the value **today** of a series of future cash flows after each one is discounted by a chosen rate (e.g. inflation or required return).  
For liabilities like student‑loan repayments, the plan with the **lower NPV** is cheaper in today's money. The default discount rate is 2 % (e.g. UK inflation target).

**Formula**

$$
\text{NPV} \;=\; \sum_{t=0}^{T} \frac{C_t}{(1 + r)^{t}}
$$

where&nbsp;  
\(C_t\) = cash flow at time \(t\) (negative = payment, positive = income)  
\(r\) = discount rate (e.g. 2 % inflation ⇒ 0.02)  
\(T\) = final period in years (or months) being analysed
""")

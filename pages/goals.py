import streamlit as st
from datetime import date
from database.database import get_session
from database.models import Goal
from services.goal_service import per_paycheck_for_goal
from services.settings_service import get_pay_frequency

st.header("Goals")

session = get_session()
try:
    goals = session.query(Goal).all()
    pay_freq = get_pay_frequency()

    if goals:
        total_saved = sum(g.current_amount for g in goals)
        total_target = sum(g.target_amount for g in goals)
        overall_pct = (total_saved / total_target * 100) if total_target else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Saved", f"${total_saved:,.2f}")
        c2.metric("Total Target", f"${total_target:,.2f}")
        c3.metric("Overall Progress", f"{overall_pct:.1f}%")

        st.markdown("---")

        for goal in goals:
            remaining = goal.target_amount - goal.current_amount
            pct = min(goal.current_amount / goal.target_amount, 1.0) if goal.target_amount else 0
            days_left = (goal.target_date - date.today()).days if goal.target_date else 0
            per_check = per_paycheck_for_goal(goal, pay_freq)

            with st.container(border=True):
                c_n, c_p, c_m, c_x = st.columns([3, 3, 2, 1])
                with c_n:
                    st.subheader(goal.goal_name)
                    if goal.notes:
                        st.caption(goal.notes)
                with c_p:
                    st.write(f"${goal.current_amount:,.2f} / ${goal.target_amount:,.2f}")
                    st.progress(pct)
                    st.caption(f"${remaining:,.2f} remaining")
                with c_m:
                    st.write(f"Target: {goal.target_date}")
                    st.write(f"{days_left} days left")
                    st.write(f"${per_check:,.2f}/paycheck")
                if c_x.button("X", key=f"del_goal_{goal.id}"):
                    session.query(Goal).filter(Goal.id == goal.id).delete()
                    session.commit()
                    st.rerun()
    else:
        st.info("No savings goals yet. Add your first goal below.")

    st.markdown("---")
    st.subheader("Add Goal")
    with st.form("add_goal_form"):
        c_a, c_b = st.columns(2)
        name = c_a.text_input("Goal Name")
        target = c_a.number_input("Target Amount ($)", min_value=0.0, step=100.0)
        current = c_b.number_input("Current Amount ($)", min_value=0.0, step=10.0)
        target_date = c_b.date_input("Target Date")
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("Add Goal") and name:
            session.add(Goal(
                goal_name=name, target_amount=target,
                current_amount=current, target_date=target_date, notes=notes,
            ))
            session.commit()
            st.success(f"Added: {name}")
            st.rerun()
finally:
    session.close()

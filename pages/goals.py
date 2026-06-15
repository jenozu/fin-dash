import streamlit as st
from datetime import date
from database.database import get_session
from database.models import Goal, GoalDeposit
from services.goal_service import (
    get_all_goals,
    per_paycheck_for_goal,
    update_goal,
    deposit_to_goal,
    get_goal_deposit_history,
)
from services.settings_service import get_pay_frequency

if "editing_goal_id" not in st.session_state:
    st.session_state["editing_goal_id"] = None
if "depositing_goal_id" not in st.session_state:
    st.session_state["depositing_goal_id"] = None

st.header("Goals")

today = date.today()
pay_freq = get_pay_frequency()
goals = get_all_goals()

if goals:
    total_saved = sum(g.current_amount for g in goals)
    total_target = sum(g.target_amount for g in goals)
    overall_pct = (total_saved / total_target * 100) if total_target else 0
    active_count = sum(
        1 for g in goals
        if g.current_amount < g.target_amount and g.target_date and g.target_date >= today
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Saved", f"${total_saved:,.2f}")
    c2.metric("Total Target", f"${total_target:,.2f}")
    c3.metric("Overall Progress", f"{overall_pct:.1f}%")
    c4.metric("Active Goals", active_count)

    st.markdown("---")

    for goal in goals:
        remaining = max(goal.target_amount - goal.current_amount, 0.0)
        pct = min(goal.current_amount / goal.target_amount, 1.0) if goal.target_amount else 0
        per_check = per_paycheck_for_goal(goal, pay_freq)
        editing = st.session_state["editing_goal_id"] == goal.id
        depositing = st.session_state["depositing_goal_id"] == goal.id

        if goal.current_amount >= goal.target_amount:
            badge_text, badge_color = "Complete", "#2ecc71"
        elif goal.target_date and goal.target_date < today:
            badge_text, badge_color = "Past Due", "#e74c3c"
        else:
            badge_text, badge_color = None, None

        with st.container(border=True):
            r1a, r1b = st.columns([5, 2])
            badge_html = ""
            if badge_text:
                badge_html = (
                    f" &nbsp;<span style='background:{badge_color};color:#fff;"
                    f"padding:2px 8px;border-radius:10px;font-size:0.78em'>{badge_text}</span>"
                )
            r1a.markdown(f"**{goal.goal_name}**{badge_html}", unsafe_allow_html=True)
            if per_check > 0:
                r1b.markdown(
                    f"<div style='text-align:right;color:#3498db'>"
                    f"${per_check:,.2f}/paycheck needed</div>",
                    unsafe_allow_html=True,
                )

            st.write(
                f"${goal.current_amount:,.2f} / ${goal.target_amount:,.2f}"
                f"  —  ${remaining:,.2f} remaining"
            )
            st.progress(pct)

            if goal.target_date:
                days_left = (goal.target_date - today).days
                if days_left < 0:
                    st.caption(f"Target: {goal.target_date}  ⚠️ past due by {abs(days_left)} days")
                else:
                    st.caption(f"Target: {goal.target_date}  ({days_left} days remaining)")
            if goal.notes:
                st.caption(goal.notes)

            _, btn_dep, btn_edit, btn_del = st.columns([4, 2, 2, 1])

            if btn_dep.button(
                "Cancel" if depositing else "Deposit",
                key=f"dep_btn_g_{goal.id}",
            ):
                st.session_state["depositing_goal_id"] = None if depositing else goal.id
                if not depositing:
                    st.session_state["editing_goal_id"] = None
                st.rerun()

            if btn_edit.button(
                "Cancel Edit" if editing else "Edit",
                key=f"edit_btn_g_{goal.id}",
            ):
                st.session_state["editing_goal_id"] = None if editing else goal.id
                if not editing:
                    st.session_state["depositing_goal_id"] = None
                st.rerun()

            if btn_del.button("✕", key=f"del_goal_{goal.id}"):
                session = get_session()
                try:
                    session.query(GoalDeposit).filter(GoalDeposit.goal_id == goal.id).delete()
                    session.query(Goal).filter(Goal.id == goal.id).delete()
                    session.commit()
                finally:
                    session.close()
                if st.session_state["editing_goal_id"] == goal.id:
                    st.session_state["editing_goal_id"] = None
                if st.session_state["depositing_goal_id"] == goal.id:
                    st.session_state["depositing_goal_id"] = None
                st.rerun()

            if depositing:
                with st.form(f"deposit_form_g_{goal.id}"):
                    dep_amount = st.number_input(
                        "Deposit Amount ($)", min_value=0.01, step=10.0, format="%.2f",
                    )
                    dep_notes = st.text_input("Notes (optional)")
                    ds, dc = st.columns(2)
                    dep_saved = ds.form_submit_button("Add Deposit")
                    dep_cancel = dc.form_submit_button("Cancel")
                    if dep_saved:
                        if dep_amount > 0:
                            deposit_to_goal(goal.id, dep_amount, dep_notes)
                            st.session_state["depositing_goal_id"] = None
                            st.rerun()
                        else:
                            st.warning("Enter an amount greater than $0.")
                    if dep_cancel:
                        st.session_state["depositing_goal_id"] = None
                        st.rerun()

            if editing:
                with st.form(f"edit_form_g_{goal.id}"):
                    ec1, ec2 = st.columns(2)
                    new_name = ec1.text_input("Goal Name", value=goal.goal_name)
                    new_target = ec1.number_input(
                        "Target Amount ($)", min_value=0.0,
                        value=float(goal.target_amount), step=100.0,
                    )
                    new_current = ec2.number_input(
                        "Current Amount ($)", min_value=0.0,
                        value=float(goal.current_amount), step=10.0,
                    )
                    new_date = ec2.date_input("Target Date", value=goal.target_date)
                    new_notes = st.text_input("Notes", value=goal.notes or "")
                    es, ec = st.columns(2)
                    edit_saved = es.form_submit_button("Save Changes")
                    edit_cancel = ec.form_submit_button("Cancel")
                    if edit_saved:
                        if new_name:
                            update_goal(goal.id, new_name, new_target, new_current, new_date, new_notes)
                            st.session_state["editing_goal_id"] = None
                            st.rerun()
                        else:
                            st.warning("Goal name is required.")
                    if edit_cancel:
                        st.session_state["editing_goal_id"] = None
                        st.rerun()

            with st.expander("Contribution History"):
                history = get_goal_deposit_history(goal.id)
                if history:
                    for d in history:
                        note = f" — {d.notes}" if d.notes else ""
                        st.write(f"{d.deposit_date} — +${d.amount:,.2f}{note}")
                else:
                    st.write("No contributions recorded yet. Use Deposit to log savings.")
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
        session = get_session()
        try:
            session.add(Goal(
                goal_name=name, target_amount=target,
                current_amount=current, target_date=target_date, notes=notes,
            ))
            session.commit()
        finally:
            session.close()
        st.success(f"Added: {name}")
        st.rerun()

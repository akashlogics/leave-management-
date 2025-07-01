import frappe
from frappe.utils import get_url, nowdate, add_days

def weekly_pending_leave_summary():
    """Send a weekly summary email of all pending leave approvals."""
    pending = frappe.get_all("leave application", filters={
        "status": "Pending Approval",
        "docstatus": 0
    }, fields=["name", "employee", "from_date", "to__date"])

    if not pending:
        return

    message = "<h3>Weekly Summary: Pending Leave Approvals</h3><ul>"
    for leave in pending:
        url = get_url(f"/app/leave%20application/{leave.name}")
        message += f"<li><b>{leave.name}</b> - {leave.employee} ({leave.from_date} to {leave.to__date}) – <a href='{url}'>View</a></li>"
    message += "</ul>"

    emails = get_approver_emails()

    if emails:
        frappe.sendmail(
            recipients=emails,
            subject="Weekly Pending Leave Applications Summary",
            message=message
        )

def monthly_leave_balance_update():
    """Automatically update leave balances monthly."""
    employees = frappe.get_all("employee_rd", fields=["name", "joining_date", "leave_balance"])

    for emp in employees:
        # 1.5 leaves accrue per month
        new_balance = (emp.leave_balance or 0) + 1.5
        frappe.db.set_value("employee_rd", emp.name, "leave_balance", new_balance)

    frappe.db.commit()

def get_approver_emails():
    """Get all leave approver emails"""
    approvers = frappe.get_all("User",
        filters={"roles.role": "Leave Approver"},
        pluck="email"
    )
    return [e for e in approvers if e]

def daily_leave_balance_check():
    """Check and notify employees with low leave balances"""
    low_balance_limit = 3.0  # Threshold for notification
    employees = frappe.get_all("employee_rd",
        filters={"leave_balance": ["<", low_balance_limit]},
        fields=["name", "employee_name", "leave_balance", "user_id"]
    )

    for emp in employees:
        if emp.user_id:
            frappe.sendmail(
                recipients=emp.user_id,
                subject="Low Leave Balance Alert",
                message=f"Hello {emp.employee_name}, your current leave balance is {emp.leave_balance} which is below the minimum threshold of {low_balance_limit} days."
            )

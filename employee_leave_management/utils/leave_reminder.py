import frappe
from frappe.utils import get_url

def send_pending_leave_reminders():
    pending = frappe.get_all("leave application", filters={
        "status": "Pending Approval",
        "docstatus": 0
    }, fields=["name", "employee", "from_date", "to__date"])

    if not pending:
        return

    approver_emails = frappe.get_all("User", filters={
        "roles.role": "Leave Approver"
    }, fields=["email"])

    emails = [user["email"] for user in approver_emails if user.get("email")]
    if not emails:
        return

    # Group leaves by approver
    approvers = frappe.get_all("User",
        filters={"roles.role": "Leave Approver"},
        fields=["email", "name"])
        
    for approver in approvers:
        leaves = [l for l in pending if l.owner == approver.name]
        if not leaves:
            continue
            
        content = []
        for leave in leaves:
            days_pending = frappe.utils.date_diff(frappe.utils.nowdate(), leave.creation)
            leave_url = get_url(f"/app/leave%20application/{leave.name}")
            content.append(f"""
                <li>
                    <a href="{leave_url}">{leave.name}</a> - {leave.employee}<br>
                    Dates: {leave.from_date} to {leave.to_date}<br>
                    Pending for: {days_pending} days
                </li>
            """)
            
        frappe.sendmail(
            recipients=[approver.email],
            subject=f"Pending Leave Approvals ({len(leaves)})",
            message=f"""
                <p>You have {len(leaves)} leave applications pending approval:</p>
                <ul>{"".join(content)}</ul>
                <p>Please review these at your earliest convenience.</p>
            """
        )

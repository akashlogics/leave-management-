import frappe
from frappe.utils import get_url, nowdate, add_days, get_datetime
from frappe.core.doctype.communication.email import make
from employee_leave_management.leave_management.doctype.leave_application.leave_application import leaveapplication

def send_pending_leave_reminders():
    """Send reminders for leave applications pending over 24 hours"""
    try:
        pending_apps = frappe.get_all("Leave Application",
            filters={
                "status": "Pending Approval",
                "modified": ["<", get_datetime(add_days(nowdate(), -1))]
            },
            fields=["name"]
        )

        for app in pending_apps:
            doc = frappe.get_doc("Leave Application", app.name)
            if doc and hasattr(doc, "send_reminder"):
                doc.send_reminder()
                
    except Exception as e:
        frappe.log_error(f"Pending leave reminder error: {str(e)}")

def send_daily_approval_reminders():
    """Daily digest email for approvers with pending requests"""
    try:
        pending = frappe.get_all("Leave Application",
            filters={"status": "Pending Approval"},
            fields=["name", "employee", "from_date", "to__date", "approver"]
        )

        if not pending:
            return

        html_content = """
            <h3>Pending Leave Approvals ({count})</h3>
            <ul>{items}</ul>
            <p><a href="{portal_url}">View All Pending Requests</a></p>
        """.format(
            count=len(pending),
            items="\n".join(
                f"<li>{app.employee}: {app.from_date} to {app.to__date} ({frappe.utils.get_link_to_form('Leave Application', app.name)})</li>"
                for app in pending
            ),
            portal_url=get_url("/app/leave-application")
        )

        approvers = frappe.get_all("User",
            filters={"role_profile_name": "Leave Approver"},
            pluck="email"
        )

        if approvers:
            frappe.sendmail(
                recipients=approvers,
                subject=f"Daily Leave Approval Digest ({len(pending)} pending)",
                message=html_content,
                now=True
            )

    except Exception as e:
        frappe.log_error(f"Daily approval reminder error: {str(e)}")
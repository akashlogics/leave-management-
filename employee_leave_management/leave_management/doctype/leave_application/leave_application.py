# Copyright (c) 2025, akash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, date_diff, get_url_to_form, nowdate
from frappe import _, throw
from frappe.core.doctype.communication.email import make
from frappe import sendmail, _, enqueue

class leaveapplication(Document):

    def validate(self):
        self.validate_dates()
        self.validate_employee()
        self.validate_leave_overlap()
        self.set_approver()
        self.set_status()

    def set_approver(self):
        """Set approver based on employee's reporting manager"""
        if not self.approver:
            employee = frappe.get_doc("employee_rd", self.employee)
            if not employee.reporting_manager:
                frappe.throw(_("No reporting manager assigned for employee {0}").format(self.employee))
            self.approver = employee.reporting_manager

    def before_submit(self):
        if self.status == "Approved":
            self.update_leave_balance()

    def update_leave_balance(self):
        employee = frappe.get_doc("employee_rd", self.employee)
        employee.leave_balance -= self.total_days
        employee.save()

    def validate_dates(self):
        if getdate(self.from_date) > getdate(self.to__date):
            throw(_("From Date cannot be after To Date"))

        self.total_days = date_diff(self.to__date, self.from_date) + 1

    def validate_employee(self):
        if not frappe.db.exists("employee_rd", self.employee):
            throw(_("Invalid Employee ID"))

    def validate_leave_overlap(self):
        overlaps = frappe.db.sql("""
            SELECT name FROM `tableave application`
            WHERE employee = %s
            AND (
                (from_date <= %s AND to__date >= %s)
                OR (from_date <= %s AND to__date >= %s)
            )
            AND name != %s AND docstatus < 2
        """, (self.employee, self.from_date, self.from_date, self.to__date, self.to__date, self.name))

        if overlaps:
            throw(_("Leave overlaps with existing approved leave application: {0}").format(overlaps[0][0]))

    def set_status(self):
        if self.docstatus == 0:
            if "Leave Approver" in frappe.get_roles():
                self.status = "Approved"
            else:
                self.status = "Pending Approval"

    def validate_leave_balance(self):
        """Validate leave balance before submission"""
        leave_days = date_diff(self.to__date, self.from_date) + 1
        employee = frappe.get_doc("employee_rd", self.employee)
        if employee.leave_balance < leave_days:
            frappe.throw(_("Insufficient leave balance. Available: {0} days").format(employee.leave_balance))

    def update_leave_balance_after_approval(self):
        """Update leave balance after approval"""
        leave_days = date_diff(self.to__date, self.from_date) + 1
        employee = frappe.get_doc("employee_rd", self.employee)
        employee.leave_balance -= leave_days
        employee.save()

    def on_submit(self):
        if self.status == "Approved":
            self.send_leave_notification(
                subject="Leave Application Approved",
                message=f"""Your leave from {self.from_date} to {self.to__date} has been approved.
                {date_diff(self.to__date, self.from_date) + 1} days deducted from your balance."""
            )
        elif self.status == "Rejected":
            self.send_status_notification("rejected")

    def on_cancel(self):
        if self.status == "Approved":
            employee_doc = frappe.get_doc("employee_rd", self.employee)
            employee_doc.leave_balance += self.total_days
            employee_doc.save()
            frappe.msgprint(_("Restored {0} days to leave balance").format(self.total_days))

    def calculate_leave_balance(self):
        employee_doc = frappe.get_doc("employee_rd", self.employee)
        return employee_doc.leave_balance

    def get_leave_history(self):
        leaves = frappe.db.sql("""
            SELECT name, from_date, to_date, status, leave_type
            FROM `tableave application`
            WHERE employee = %s
            AND docstatus = 1
            ORDER BY from_date DESC
        """, self.employee, as_dict=True)

        return {
            "total_leaves": len(leaves),
            "approved_leaves": len([l for l in leaves if l.status == "Approved"]),
            "pending_leaves": len([l for l in leaves if l.status == "Pending Approval"]),
            "details": leaves
        }
    def send_leave_notification(self, subject, message):
        if not self.employee:
            return

        # Get email of the employee (assuming email is a field in employee_rd)
        employee_doc = frappe.get_doc("employee_rd", self.employee)
        email = employee_doc.get("email") or frappe.session.user

        frappe.sendmail(
            recipients=email,
            subject=subject,
            message=message,
            reference_doctype=self.doctype,
            reference_name=self.name
        )

    def after_insert(self):
        self.schedule_reminders()

    def send_status_notification(self, status):
        """Send email notification for approval/rejection"""
        template = "leave_status"
        employee = frappe.get_doc("employee_rd", self.employee)

        args = {
            "status": status,
            "employee_name": employee.employee_name,
            "from_date": self.from_date,
            "to_date": self.to__date,
            "total_days": self.total_days,
            "link": get_url_to_form(self.doctype, self.name)
        }

        make(
            subject=f"Leave Application {status.capitalize()} - {self.name}",
            content=frappe.render_template(templates[template], args),
            recipients=employee.email,
            reference_doctype=self.doctype,
            reference_name=self.name
        ).insert(ignore_permissions=True)

    def send_reminder(self):
        """Send reminder to approver"""
        template = "leave_reminder"
        approver = frappe.get_doc("User", self.approver)

        args = {
            "employee": self.employee,
            "days_pending": (getdate(nowdate()) - getdate(self.creation)).days,
            "link": get_url_to_form(self.doctype, self.name)
        }

        make(
            subject=f"Reminder: Pending Leave Application ({self.name})",
            content=frappe.render_template(templates[template], args),
            recipients=approver.email,
            reference_doctype=self.doctype,
            reference_name=self.name
        ).insert(ignore_permissions=True)

    def schedule_reminders(self):
        """Enqueue daily reminder checks"""
        enqueue(
            "employee_leave_management.leave_management.doctype.leave_application.leaveapplication.check_pending_approvals",
            queue="long",
            timeout=150
        )

@frappe.whitelist()
def check_pending_approvals():
    """Check for pending approvals older than 1 day"""
    pending = frappe.get_all("Leave Application",
        filters={"status": "Pending Approval", "creation": ["<", add_days(nowdate(), -1)]},
        fields=["name"]
    )

    for app in pending:
        doc = frappe.get_doc("Leave Application", app.name)
        doc.send_reminder()

templates = {
    "leave_status": '''
        <p>Dear {{ employee_name }},</p>
        <p>Your leave application from {{ from_date }} to {{ to_date }} has been <strong>{{ status }}</strong>.</p>
        {% if status == "approved" %}
        <p>{{ total_days }} days have been deducted from your leave balance.</p>
        {% endif %}
        <p>View details: <a href="{{ link }}">{{ link }}</a></p>
    ''',
    "leave_reminder": '''
        <p>Dear Approver,</p>
        <p>Leave application from {{ employee }} has been pending for {{ days_pending }} days.</p>
        <p>Please review: <a href="{{ link }}">{{ link }}</a></p>
    '''
}
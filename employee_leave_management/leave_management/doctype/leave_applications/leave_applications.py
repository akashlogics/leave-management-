# Copyright (c) 2025, akash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff

class LeaveApplications(Document):
	def validate(self):
		# Always validate dates and leave type
		if self.time_leaves:
			if self.from_date != self.to_date:
				frappe.throw("Time-based leaves must be for a single day")
		elif self.from_date and self.to_date:
			if self.from_date > self.to_date:
				frappe.throw("From Date cannot be after To Date")

		# Only calculate leave days for approved applications
		status_value = getattr(self, "status", None) or getattr(self, "status_update", None)
		if status_value == "Approved":
			if self.time_leaves:
				time_map = {
					"2 hours": 0.25,
					"Half day": 0.5,
					"1 full day": 1.0
				}
				self.total_leave_days = time_map.get(self.time_leaves, 0)
			else:
				self.total_leave_days = date_diff(self.to_date, self.from_date) + 1
		else:
			# Reset leave days for non-approved statuses
			self.total_leave_days = 0

	def validate(self):
		# Existing date validation logic here...

		# Sync status_update to core status field
		if hasattr(self, "status_update"):
			self.status = self.status_update

		# Prevent approving draft documents
		if self.docstatus == 0 and self.status == "Approved":
			frappe.throw("Cannot approve leave application while in draft state")

		# Check email config for approved/rejected status
		#if self.status in ["Approved", "Rejected"]:
		#	if not frappe.db.get_value("Email Account", {"default_outgoing": 1}):
		#		frappe.throw(
		#			"Please setup default outgoing Email Account from: <br>"
		#			"<button class='btn btn-xs btn-primary' onclick='frappe.set_route(\"Form\", \"Email Account\")'>"
		#			"Create Email Account</button>",
		#			title="Email Configuration Required"
		#		)

	def on_submit(self):
		if self.status != "Approved":
			frappe.throw("Only Approved applications can be submitted")
			
		# Final validation before submission
		self.check_email_configuration()
		self.update_employee_leave_balance()
		self.send_status_notification(self.status)

	#def check_email_configuration(self):
	#	if not frappe.db.get_value("Email Account", {"default_outgoing": 1}):
	#		frappe.throw(
	#			"Please setup default outgoing Email Account from: <br>"
	#			"<button class='btn btn-xs btn-primary' onclick='frappe.set_route(\"Form\", \"Email Account\")'>"
	#			"Create Email Account</button>",
	#			title="Email Configuration Required"
	#		)

	def on_cancel(self):
		prev_status = getattr(self, "_doc_before_save", {}).get("status") or getattr(self, "_doc_before_save", {}).get("status_update")
		if prev_status == "Approved":
			self.restore_employee_leave_balance()
		self.send_status_notification("Cancelled")

	def update_employee_leave_balance(self):
		"""Deduct leave days from employee's balance"""
		employee = frappe.get_doc("Employee List", self.employee)
		employee.available_leave_days -= self.total_leave_days
		employee.save()

	def restore_employee_leave_balance(self):
		"""Restore leave days when application is cancelled"""
		employee = frappe.get_doc("Employee List", self.employee)
		employee.available_leave_days += self.total_leave_days
		employee.save()

	#def send_status_notification(self):
	#	"""Send email notification to employee about status change"""
	#	try:
	#		frappe.sendmail(
	#			recipients=self.email,
	#			subject=f"Leave Application {self.status}",
	#			message=f"Your leave application {self.name} has been {self.status.lower()}",
	#			now=True
	#		)
	#	except frappe.OutgoingEmailError:
	#		frappe.msgprint(
	#			"Failed to send notification email. Please check email configuration.",
	#			indicator="orange",
	#			alert=True
	#		)
		#	else:
		#		self.send_status_notification()
		#		# Sync status_update to status if present
		#		if hasattr(self, "status_update"):
		#			self.status = self.status_update

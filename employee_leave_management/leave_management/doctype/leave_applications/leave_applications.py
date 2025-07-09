# Copyright (c) 2025, akash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, getdate

class LeaveApplications(Document):
	def validate(self):
		self.validate_leave_dates()
		self.validate_leave_type()
		self.total_leave_days = self.get_total_days()
		self.before_submit()
		
	def validate_leave_dates(self):
		if self.leave_type == "Others":
			if self.from_date != self.to_date:
				frappe.throw("From Date and To Date must be the same for 'Others' leave type")
		elif self.from_date > self.to_date:
			frappe.throw("From Date must be earlier than To Date")

	def validate_leave_type(self):
		if not self.leave_type:
			frappe.throw("Leave Type cannot be empty")
		valid_types = ["Sick Leave", "Casual Leave", "Annual Leave", "Others"]
		if self.leave_type not in valid_types:
			frappe.throw(f"Invalid Leave Type: {self.leave_type}. Must be one of {', '.join(valid_types)}")

	def get_total_days(self):
		if self.leave_type == "Others":
			return {
				"2 hours": 0.25,
				"Half day": 0.5,
				"1 full day": 1
			}.get(self.time_leaves, 0)
		return date_diff(self.to_date, self.from_date) + 1
	
	def update_leave_status_on_submit(doc, method):
		"""Update the leave status for the employee when a leave application is submitted."""
		if doc.status == "Approved":
			doc.update_leave_status()
		else:
			frappe.throw("Leave application must be approved to update leave status.")
		# Get allocated leaves from Leave Allocation document
		allocated_leaves = frappe.get_value("Leave Allocation",
			{
				"employee_id": doc.employee,
				"month": doc.month,
				"docstatus": 1
			},
			"leave_allowed"
		)
		
		if not allocated_leaves:
			frappe.throw(f"No valid leave allocation found for {doc.employee} (Month: {doc.month})")

		frappe.db.set_value("Employee Leave Status",
			{
				"employee": doc.employee,
				"month": doc.month
			},
			{
				"leaves_used": doc.total_leave_days,
				"leave_remaining": allocated_leaves - doc.total_leave_days,
				"leave_allocated": allocated_leaves
			}
		)

	def before_submit(self):
		user_roles = frappe.get_roles()
		if "Employee" in user_roles:
			if self.status in ["Approved", "Pending", "Pending Approval"]:
				frappe.throw(f"Employees cannot submit applications with status '{self.status}'. Status must be set through approval workflow")
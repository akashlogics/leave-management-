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
	
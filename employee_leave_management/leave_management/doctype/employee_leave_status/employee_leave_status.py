# Copyright (c) 2025, akash and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document

class EmployeeLeaveStatus(Document):
	def validate(self):
		self.calculate_leave_usage()
		self.calculate_remaining_leaves()
		self.validate_allocation()

	def calculate_leave_usage(self):
		leaves_used = frappe.db.sql("""
			SELECT COALESCE(SUM(total_leave_days), 0)
			FROM `tabLeave Applications`
			WHERE employee = %s
			  AND month = %s
			  AND docstatus = 1
		""", (self.employee, self.month))
		
		self.leaves_used = flt(leaves_used[0][0]) if leaves_used else 0
	
	def calculate_remaining_leaves(self):
		self.leave_remaining = flt(self.leave_allocated) - flt(self.leaves_used)

	def validate_allocation(self):
		if not self.leave_allocated:
			frappe.throw("Leave Allocation is required")
		if flt(self.leave_allocated) < 0:
			frappe.throw("Leave Allocation cannot be negative")

# Copyright (c) 2025, akash and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document


class EmployeeLeaveStatus(Document):
	def validate(self):
		self.update_leave_usage()

	def update_leave_usage(self):
		leaves_used = frappe.db.sql("""
			SELECT SUM(total_leave_days)
			FROM `tabLeave Applications`
			WHERE employee = %s
				AND status = 'Approved'
				AND docstatus = 1
		""", self.employee)
		
		self.leaves_used = flt(leaves_used[0][0]) if leaves_used else 0
		self.leave_remaining = flt(self.leave_allocated) - self.leaves_used

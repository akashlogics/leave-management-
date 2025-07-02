# Copyright (c) 2025, akash and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document


class EmployeeLeaveStatus(Document):
	def validate(self):
		self.update_leave_usage()

	def update_leave_usage(self):
		count=frappe.db.sum('Leave Applications', {
			'employee': self.employee,
			'status_update': 'Approved'
		})
		self.leaves_used = count
# Copyright (c) 2025, akash and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = [
		{"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": "Leave Type", "fieldname": "leave_type", "fieldtype": "Link", "options": "Leave Type", "width": 120},
		{"label": "Total Leave Days", "fieldname": "total_leave_days", "fieldtype": "Float", "width": 100},
		{"label": "Used Leave Days", "fieldname": "used_leave_days", "fieldtype": "Float", "width": 100},
		{"label": "Remaining Leave Days", "fieldname": "remaining_leave_days", "fieldtype": "Float", "width": 100},
	]

	conditions = "1=1"
	if filters.get("employee"):
		conditions += " AND employee = %(employee)s"
	if filters.get("leave_type"):
		conditions += " AND leave_type = %(leave_type)s"

	data = frappe.db.sql(f"""
		SELECT
			employee,
			leave_type,
			total_leave_days,
			used_leave_days,
			remaining_leave_days
		FROM `tabLeave Balance`
		WHERE docstatus < 2 {conditions}
		ORDER BY employee, leave_type
	""", filters, as_dict=True)

	return columns, data
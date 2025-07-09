# Copyright (c) 2025, akash and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = [
		{"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": "Leave Type", "fieldname": "leave_type", "fieldtype": "Link", "options": "Leave Type", "width": 120},
		{"label": "Total Leave Days", "fieldname": "leave_allocated", "fieldtype": "Float", "width": 100},
		{"label": "Used Leave Days", "fieldname": "leaves_used", "fieldtype": "Float", "width": 100},
		{"label": "Remaining Leave Days", "fieldname": "leave_remaining", "fieldtype": "Float", "width": 100},
	]

	#conditions = []
	#if filters.get("employee"):
	#	conditions.append("employee = %(employee)s")
	#if filters.get("leave_type"):
	#	conditions.append("leave_type = %(leave_type)s")
	#
	#conditions = " AND ".join(conditions)
	#if conditions:
	#	conditions = " AND " + conditions
#
	data = frappe.get_all(
		"Leave Application",
		filters=filters,
		fields=['employee', 'leave_type', 'leave_allocated', 'leaves_used', 'leave_remaining'],
		order_by="employee"
	)

	#data = frappe.db.sql(f"""
	#	SELECT
	#		employee,
	#		leave_type,
	#		leave_allocated,
	#		leaves_used,
	#		leave_remaining
	#	FROM `tabEmployee Leave Status`
	#	WHERE docstatus = 0
	#""", filters, as_dict=True)
#
	#return columns, data

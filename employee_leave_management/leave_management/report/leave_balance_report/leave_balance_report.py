# Copyright (c) 2025, akash and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee List", "width": 150},
        {"label": "Month", "fieldname": "month", "fieldtype": "Select", "width": 120},
        {"label": "Leave Allocated", "fieldname": "leave_allocated", "fieldtype": "Float", "width": 120},
        {"label": "Leaves Used", "fieldname": "leaves_used", "fieldtype": "Float", "width": 120},
        {"label": "Remaining Leaves", "fieldname": "leave_remaining", "fieldtype": "Float", "width": 120},
    ]

    data = frappe.get_all(
        "Employee Leave Status",
        fields=["employee", "month", "leave_allocated", "leaves_used", "leave_remaining"],
        filters=filters,
        order_by="employee, month"
    )

    return columns, data
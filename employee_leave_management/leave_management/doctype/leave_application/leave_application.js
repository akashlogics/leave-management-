frappe.ui.form.on('Leave Application', {
    refresh(frm) {
        frm.set_query('employee', () => {
            return {
                filters: {
                    'status': 'Active'
                }
            };
        });
        
        // Add approval buttons for managers
        if(frm.doc.status === "Open" && frappe.user.has_role("Manager")) {
            frm.add_custom_button(__("Approve"), () => frm.events.approve_application(frm));
            frm.add_custom_button(__("Reject"), () => frm.events.reject_application(frm));
        }
    },

    approve_application(frm) {
        frappe.call({
            method: "employee_leave_management.hr_managers.doctype.manager1.manager1.approve_leave",
            args: {
                application: frm.doc.name
            },
            callback: () => frm.refresh()
        });
    },

    reject_application(frm) {
        frappe.call({
            method: "employee_leave_management.hr_managers.doctype.manager1.manager1.reject_leave",
            args: {
                application: frm.doc.name
            },
            callback: () => frm.refresh()
        });
    },
    
    before_submit(frm) {
        if(!frm.doc.approver) {
            frappe.throw(__("Please select an approver before submitting"));
        }
    },

    employee(frm) {
        if(frm.doc.employee) {
            frappe.db.get_value('employee_rd', frm.doc.employee, 'leave_balance')
            .then(r => {
                frm.set_value('leave_balance', r.message.leave_balance);
            });
        }
    },
    
    from_date(frm) {
        validate_date_overlap(frm);
    },
    
    to_date(frm) {
        validate_date_overlap(frm);
    }
});

function validate_date_overlap(frm) {
    if(frm.doc.from_date && frm.doc.to_date) {
        frappe.call({
            method: 'employee_leave_management.leave_management.doctype.leave_application.leave_application.check_overlapping_leaves',
            args: {
                employee: frm.doc.employee,
                from_date: frm.doc.from_date,
                to_date: frm.doc.to_date,
                exclude_name: frm.doc.name
            },
            callback: (r) => {
                if(r.message) {
                    frappe.throw(__('Leave overlaps with existing approved leave application: {0}', [r.message]));
                }
            }
        });
    }
}

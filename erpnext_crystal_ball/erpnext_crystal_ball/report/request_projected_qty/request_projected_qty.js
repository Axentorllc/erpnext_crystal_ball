// Copyright (c) 2024, Carlos and contributors
// For license information, please see license.txt

frappe.query_reports["Request Projected Qty"] = {
	"filters": [

	],
	onload: function(report) {
		report.page.add_inner_button(__('Material Request'), function() {
			frappe.msgprint(__('Processing Material Request...'));
			
			frappe.call({
				method: "erpnext_crystal_ball.erpnext_crystal_ball.report.request_projected_qty.request_projected_qty.order_material_request",
				callback: function(r) {
			
					if (r.message === "success") {
						frappe.msgprint(__('Material Request created successfully.'));
						frappe.set_route('Form', 'Material Request');
					} else {
						frappe.msgprint(__('Failed to create Material Request.'));
					}
				}
			});
		},)
	},

};



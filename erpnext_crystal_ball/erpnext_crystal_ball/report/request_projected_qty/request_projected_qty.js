// Copyright (c) 2024, Carlos and contributors
// For license information, please see license.txt

frappe.query_reports["Request Projected Qty"] = {
	"filters": [
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			reqd: 1
		},
		{
			fieldname: "safety_stock",
			label: __("Include Safety Stock"),
			fieldtype: "Check",
		},
	],

	// Function to fetch all filter values as parameters
	get_filters_as_params: function() {
		let filters = {};
		this.filters.forEach(filter => {
			filters[filter.fieldname] = frappe.query_report.get_filter_value(filter.fieldname);
		});
		return filters;
	},

	onload: function(report) {

		report.page.add_inner_button(__('Material Request'), function() {
			frappe.msgprint(__('Processing Material Request...'));
			
			let filters_as_params = frappe.query_reports["Request Projected Qty"].get_filters_as_params();
			
			frappe.call({
				method: "erpnext_crystal_ball.erpnext_crystal_ball.report.request_projected_qty.request_projected_qty.order_material_request",
				args: {
					filters: filters_as_params
				},
				freeze: true,
				freeze_message: "Processing Material Request... ...",
				callback: function(r) {
					if (r.message) {
						frappe.msgprint(__('Material Request created successfully.'));
						frappe.set_route('Form', 'Material Request', r.message);
					} else {
						frappe.msgprint(__('Failed to create Material Request.'));
					}
				}
			});
		});
	},
};

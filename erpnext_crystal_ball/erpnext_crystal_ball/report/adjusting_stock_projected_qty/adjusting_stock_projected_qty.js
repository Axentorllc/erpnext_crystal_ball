// Copyright (c) 2024, Carlos and contributors
// For license information, please see license.txt

frappe.query_reports["Adjusting Stock Projected Qty"] = {
	"filters": [
		{
			fieldname: "order_date",
			label: __("Order Date"),
			fieldtype: "Date",
			
		},
		// {
		// 	fieldname: "expected_date",
		// 	label: __("Expected Date"),
		// 	fieldtype: "Date",
			
		// },

	]
};

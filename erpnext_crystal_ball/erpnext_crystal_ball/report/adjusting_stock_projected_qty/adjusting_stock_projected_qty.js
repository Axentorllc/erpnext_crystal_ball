// Copyright (c) 2024, Carlos and contributors
// For license information, please see license.txt

frappe.query_reports["Adjusting Stock Projected Qty"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd:1
			
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd:1
			
		},
		{
			fieldname: "material_type",
			label: __("Group_by"),
			fieldtype: "Select",
			options: "\nRaw Material\nPack Material",
			// reqd:1
			
		},
	]
};

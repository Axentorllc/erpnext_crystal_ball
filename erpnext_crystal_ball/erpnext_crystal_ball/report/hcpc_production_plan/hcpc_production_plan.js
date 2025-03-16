// Copyright (c) 2025, Carlos and contributors
// For license information, please see license.txt

frappe.query_reports["HCPC Production Plan"] = {
	"filters": [
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options:"Fiscal Year",
			reqd:1
			
		},

	]
};

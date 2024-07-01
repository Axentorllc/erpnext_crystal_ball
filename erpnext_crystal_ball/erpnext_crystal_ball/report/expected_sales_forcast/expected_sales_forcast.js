// Copyright (c) 2024, Carlos and contributors
// For license information, please see license.txt

frappe.query_reports["Expected Sales Forcast"] = {
	"filters": [
		{
			fieldname: "expected_start",
			label: __("Expected Start"),
			fieldtype: "Date",
			
		},
		{
			fieldname: "expected_end",
			label: __("Expected End"),
			fieldtype: "Date",

		},
		{
			fieldname: "posting_date",
			label: __("Posting_Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "aggregate",
			label: __("Aggregate Item Code"),
			fieldtype: "Check",

		}


	]
};

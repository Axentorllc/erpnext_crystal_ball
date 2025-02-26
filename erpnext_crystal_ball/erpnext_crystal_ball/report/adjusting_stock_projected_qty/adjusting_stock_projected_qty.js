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
			options: "\nraw material\npack material",

		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			reqd:1
		},
		{
			fieldname: "safety_stock",
			label: __("Include Safty Stock"),
			fieldtype: "Check",
		},

	],
	formatter: function (value, row, column, data, default_formatter) {
		
		let months=["January", "February", "March", "April", "May", "June",
			"July", "August", "September", "October", "November", "December"] 
		
			for (let i = 0; i < months.length; i++) {
				let month = months[i];
		
				if (column.fieldname === `${month}_diff_qty`,value) {
					let formatted_value = default_formatter(value, row, column, data);
					
					if (value < 0) {
						formatted_value = "<span style='color:Red;'>" + formatted_value + "</span>";
					}
					
					return formatted_value;
				} 
				
			}
			
			return default_formatter(value, row, column, data);

	},
};

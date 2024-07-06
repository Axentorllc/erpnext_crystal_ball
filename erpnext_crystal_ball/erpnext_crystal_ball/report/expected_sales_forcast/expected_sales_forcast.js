// Copyright (c) 2024, Carlos and contributors
// For license information, please see license.txt

frappe.query_reports["Expected Sales Forcast"] = {
	"filters": [
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options:"Fiscal Year"
			
		},
		// {
		// 	fieldname: "expected_end",
		// 	label: __("Expected End"),
		// 	fieldtype: "Date",

		// },{
		// 	fieldname: "Type",
		// 	label: __("Type"),
		// 	fieldtype: "Select",
		// 	options: ["Rolling", "Committed","Annual"]

		// },
		// {
		// 	fieldname: "lead_time",
		// 	label: __("Lead Time"),
		// 	fieldtype: "Int",
		// },
		// {
		// 	fieldname: "coeverage",
		// 	label: __("Coverage"),
		// 	fieldtype: "Int",
		// },
		// {
		// 	fieldname: "posting_date",
		// 	label: __("Posting_Date"),
		// 	fieldtype: "Date",
		// },
		{
			fieldname: "aggregate",
			label: __("Aggregate Item Code"),
			fieldtype: "Check",

		}


	],
	
	formatter: function (value, row, column, data, default_formatter) {
		
		let months=["January", "February", "March", "April", "May", "June",
			"July", "August", "September", "October", "November", "December"] 
		
			for (let i = 0; i < months.length; i++) {
				let mon = months[i];
		
				if (column.fieldname === mon && value) {
					let formatted_value = default_formatter(value, row, column, data);
					
					if (value > 0) {
						formatted_value = "<span style='color:green;'>" + formatted_value + "</span>";
					}
					
					return formatted_value;
				} 
			}
			
			return default_formatter(value, row, column, data);

		

		
	},
};
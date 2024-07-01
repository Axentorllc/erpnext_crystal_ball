// Copyright (c) 2024, Carlos and contributors
// For license information, please see license.txt


frappe.ui.form.on("Expected Sales", {
    refresh(frm) {
        console.log("--------------")
        frm.set_query("item_code", "item_records",  function(){
            return {
                "filters": [["Item","item_group", "=", "FG"]]
               
            }
        });
	},
});



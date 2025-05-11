// Copyright (c) 2025, Carlos and contributors
// For license information, please see license.txt

frappe.ui.form.on("Production Team", {
	refresh(frm) {

        frm.set_query("member", "team_member",  function(){
            return {
                "filters": [["Employee","default_shift", "=", frm.doc.shift]]
               
            }
        });

	},
});

// Copyright (c) 2024, Carlos and contributors
// For license information, please see license.txt

frappe.ui.form.on('Projected Budget', {
    onload: function(frm) {
       
        frm.fields_dict['accounts'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            return {
                filters: {
                    company: frm.doc.company  
                }
            };
        };
    },
})

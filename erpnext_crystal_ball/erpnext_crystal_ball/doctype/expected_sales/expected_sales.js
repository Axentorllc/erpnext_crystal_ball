// Copyright (c) 2024, Axentor and contributors
// For license information, please see license.txt


frappe.ui.form.on("Expected Sales", {
    refresh(frm) {

        frm.set_query("item_code", "item_records",  function(){
            return {
                "filters": [["Item","item_group", "=", "FG"]]
               
            }
        });

        console.log(frm)
	},
    
})
frappe.ui.form.on('Item records', {
    
    before_save: function(frm) {
        frm.doc.item_records.forEach(function(row) {
            // If item_code is available in the row, fetch the stock_uom
            if (row.item_code) {
                frappe.db.get_value('Item', row.item_code, 'stock_uom')
                    .then(r => {
                        if (r.message && r.message.stock_uom) {
                            // Set the stock_uom in the row
                            frappe.model.set_value(row.doctype, row.name, 'stock_uom', r.message.stock_uom);
                        }
                    });
            }
        });
    }
});

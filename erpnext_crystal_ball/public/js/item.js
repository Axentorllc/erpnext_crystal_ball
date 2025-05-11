
frappe.ui.form.on("Item", {
    custom_route(frm) {
        if (frm.doc.custom_route) {
            frappe.call({
                method: "erpnext_crystal_ball.utils.get_item_expected_time",
                args: {
                    routing: frm.doc.custom_route
                },
                callback: function(r) {
                    if (r.message !== undefined) {
                        frm.set_value("custom_expected_time", r.message);
                    }
                }
            });
            } else {
                frm.set_value("custom_expected_time", 0);
            }
    }
});


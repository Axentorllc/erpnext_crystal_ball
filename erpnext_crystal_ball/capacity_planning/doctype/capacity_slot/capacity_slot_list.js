frappe.listview_settings['Capacity Slot'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__('Start Plan'), function() {
            let dialog = new frappe.ui.Dialog({
                title: __("Set the Planing Range"),
                fields: [
                    {
                        label: __("From Date"),
                        fieldname: "from_date",
                        fieldtype: "Date",
                        reqd: 1
                    },
                    {
                        label: __("To Date"),
                        fieldname: "to_date",
                        fieldtype: "Date",
                        reqd:1
                    
                    },
                ],
                primary_action_label: __("Fetch Transactions"),
                primary_action: function(data) {
                    if (!data) return;

                    console.log(data)


                    // Convert to JavaScript Date objects for comparison
                    let from_date = new Date(data.from_date);
                    let to_date = new Date(data.to_date);

                    console.log(from_date,to_date)

                    // Validate date range
                    if (to_date < from_date) {
                        frappe.msgprint({
                            title: __("Invalid Date Range"),
                            message: __("End Time must be greater than Start Time."),
                            indicator: "red"
                        });
                        return;  // Stop execution
                    }


                    frappe.call({
                        method: 'erpnext_crystal_ball.capacity_planning.doctype.capacity_slot.capacity_slot.update_capacity_slot',
                        args: {
                            from_date: frappe.datetime.obj_to_str(from_date),
                            to_date: frappe.datetime.obj_to_str(to_date)

                        },
                        callback: function(response) {
                            if (response.message) {
                                frappe.msgprint(response.message);
                            }
                        }
                    });

                    dialog.hide();
                }
            // frappe.msgprint(__('Processing Capacity Slot...'));
        });

        dialog.show();

        });
    }
};
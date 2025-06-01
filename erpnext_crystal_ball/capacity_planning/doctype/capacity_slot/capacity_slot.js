// // Copyright (c) 2025, Carlos and contributors
// // For license information, please see license.txt


// frappe.ui.form.on("Capacity Slot", {

//     refresh(frm) {
//         console.log(frm.docname)
//         frm.add_custom_button(__("Start Plan"), function() {
//             frappe.msgprint(__('Processing Capacity Slot...'));
//         });
//     },

//     project(frm) {
//         if (frm.doc.project) {
//             frappe.call({
//                 method: "erpnext_crystal_ball.capacity_planning.doctype.capacity_slot.capacity_slot.get_item_details",
//                 args: {
//                     project: frm.doc.project
//                 },
//                 callback: function (r) {
//                     if (r.message) {
//                         frm.clear_table("item_detail");  // Clear existing rows
//                         Object.entries(r.message).forEach(([item_code, row]) => {
//                             let child = frm.add_child("item_detail");
//                             child.item = item_code;
//                             child.qty = row.qty;
//                             child.dimension = row.dimension;
//                             child.expected_time = row.expected_time;
//                             child.route = row.route;
//                         });
//                         frm.refresh_field("item_detail"); // Refresh the child table

//                         // Call to get table suggestions
//                         // frappe.call({
//                         //     method: "erpnext_crystal_ball.capacity_planning.doctype.capacity_slot.capacity_slot.get_table_suggestions",
//                         //     args: {
//                         //         items: r.message
//                         //     },
//                         //     callback: function (s) {
//                         //         if (s.message && s.message.length) {
//                         //             const options = s.message.map(opt =>
//                         //                 `Use ${opt.tables_needed} workstation(s) from ${opt.area}`
//                         //             );

//                         //             frm.set_df_property("no_of_workstation", "options", options);
//                         //             frm.refresh_field("no_of_workstation");

//                         //         } else {
//                         //             frm.set_df_property("no_of_workstation", "options", []);
//                         //             frappe.msgprint(__('No available table configuration found'));
//                         //         }
//                         //     }
//                         // });
//                     }
//                 }
//             });
//         }
//     }
//     ,
//     no_of_workstation(frm) {
//         const selected = frm.doc.no_of_workstation;
//         if (selected && selected.includes("Use")) {
//             const match = selected.match(/Use (\d+) workstation\(s\) from (.+)/);
//             console.log(match);
//             if (match) {
//                 const tables_needed = parseInt(match[1]);
//                 const area = match[2];

//                 console.log(tables_needed, area);

//                 frappe.call({
//                     method: "erpnext_crystal_ball.capacity_planning.doctype.capacity_slot.capacity_slot.update_area_availability",
//                     args: {
//                         area: area,
//                         tables_used: tables_needed
//                     },
//                     // callback: function (r) {
//                     //     if (r.message && r.message.success) {
//                     //         frappe.msgprint(`Updated availability in ${area}.`);

//                     //         // Update remaining field
//                     //         frm.set_df_property("available_workstation_qty", r.message.remaining_qty);
//                     //     } else {
//                     //         frappe.msgprint(`Failed to update availability.`);
//                     //     }
//                     // }
//                 });
//             }
//         }
//     }
// });



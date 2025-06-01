// Copyright (c) 2025, Carlos and contributors
// For license information, please see license.txt

frappe.ui.form.on("Capacity Plan", {

	refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Start Plan'), function () {
                frappe.msgprint(__('Processing Capacity Slot...'));

				if (frm.doc.get_items_from === "Sales Order") {
					project_details = frm.doc.sales_orders || [];
				}

				else if (frm.doc.get_items_from === "Project") {
					project_details = frm.doc.project_details || [];
				}

				frappe.call({
					method: 'erpnext_crystal_ball.capacity_planning.doctype.capacity_slot.capacity_slot.create_capacity_slots',
					args: {
						items: frm.doc.po_items,
						project_details: project_details,
					},
				})
            });
        }
    },


	get_project(frm) {
		frappe.call({
			method: "get_open_projects",
			doc: frm.doc,
			callback: function (r) {
				refresh_field("project_details");
			},
		});

	},
    get_sales_orders(frm) {
        frappe.call({
            method: "get_open_sales_orders",
            doc: frm.doc,
            callback: function (r) {
                refresh_field("sales_orders");
            },
        });
    },

    get_material_request(frm) {
        frappe.call({
            method: "get_pending_material_requests",
            doc: frm.doc,
            callback: function () {
                refresh_field("material_requests");
            },
        });
    },
	get_items(frm) {
		frm.clear_table("prod_plan_references");

		frappe.call({
			method: "get_items",
			freeze: true,
			doc: frm.doc,
			callback: function () {
				refresh_field("po_items");
			},
		});
	},


});

frappe.tour["Capacity Plan"] = [

	// {
	// 	fieldname: "project",
	// 	title: "Get Project",
	// 	description: _("Click on Get Project to fetch projects based on the above filters."),
	// },
	{
		fieldname: "get_items_from",
		title: "Get Items From",
		description: __(
			"Select whether to get items from a Sales Order or a Material Request. For now select <b>Sales Order</b>.\n A Production Plan can also be created manually where you can select the Items to manufacture."
		),
	},
	{
		fieldname: "get_sales_orders",
		title: "Get Sales Orders",
		description: __("Click on Get Sales Orders to fetch sales orders based on the above filters."),
	},
	{
		fieldname: "get_items",
		title: "Get Finished Goods for Manufacture",
		description: __(
			"Click on 'Get Finished Goods for Manufacture' to fetch the items from the above Sales Orders. Items only for which a BOM is present will be fetched."
		),
	},
	{
		fieldname: "po_items",
		title: "Finished Goods",
		description: __(
			"On expanding a row in the Items to Manufacture table, you'll see an option to 'Include Exploded Items'. Ticking this includes raw materials of the sub-assembly items in the production process."
		),
	},
	{
		fieldname: "include_non_stock_items",
		title: "Include Non Stock Items",
		description: __(
			"To include non-stock items in the material request planning. i.e. Items for which 'Maintain Stock' checkbox is unticked."
		),
	},
	{
		fieldname: "include_subcontracted_items",
		title: "Include Subcontracted Items",
		description: __("To add subcontracted Item's raw materials if include exploded items is disabled."),
	},
];

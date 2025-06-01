# Copyright (c) 2025, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from pypika.terms import ExistsCriterion
from frappe.utils import (
	add_days,
	ceil,
	cint,
	comma_and,
	flt,
	get_link_to_form,
	getdate,
	now_datetime,
	nowdate,
)
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details

class CapacityPlan(Document):

	@frappe.whitelist()
	def get_items(self):
		self.set("po_items", [])
		if self.get_items_from == "Sales Order":
			self.get_so_items()

		elif self.get_items_from == "Project":
			self.get_project_items()


	def get_so_items(self):
		# Check for empty table or empty rows
		if not self.get("sales_orders") or not self.get_req_list("sales_order", "sales_orders"):
			frappe.throw(_("Please fill the Sales Orders table"), title=_("Sales Orders Required"))

		so_list = self.get_req_list("sales_order", "sales_orders")

		bom = frappe.qb.DocType("BOM")
		so_item = frappe.qb.DocType("Sales Order Item")

		items_subquery = frappe.qb.from_(bom).select(bom.name).where(bom.is_active == 1)
		items_query = (
			frappe.qb.from_(so_item)
			.select(
				so_item.parent,
				so_item.item_code,
				so_item.warehouse,
				so_item.qty,
				so_item.work_order_qty,
				so_item.delivered_qty,
 				so_item.conversion_factor,
				so_item.description,
				so_item.name,
				so_item.bom_no,
			)
			.distinct()
			.where(
				(so_item.parent.isin(so_list))
				& (so_item.docstatus == 1)
				& (so_item.qty > so_item.work_order_qty)
			)
		)

		if self.item_code and frappe.db.exists("Item", self.item_code):
			items_query = items_query.where(so_item.item_code == self.item_code)
			items_subquery = items_subquery.where(
				self.get_bom_item_condition() or bom.item == so_item.item_code
			)

		items_query = items_query.where(ExistsCriterion(items_subquery))

		items = items_query.run(as_dict=True)

		for item in items:
			item.pending_qty = (
				flt(item.qty) - max(item.work_order_qty, item.delivered_qty, 0) * item.conversion_factor
			)

		pi = frappe.qb.DocType("Packed Item")

		packed_items_query = (
			frappe.qb.from_(so_item)
			.from_(pi)
			.select(
				pi.parent,
				pi.item_code,
				pi.warehouse.as_("warehouse"),
				(((so_item.qty - so_item.work_order_qty) * pi.qty) / so_item.qty).as_("pending_qty"),
				pi.parent_item,
				pi.description,
				so_item.name,
			)
			.distinct()
			.where(
				(so_item.parent == pi.parent)
				& (so_item.docstatus == 1)
				& (pi.parent_item == so_item.item_code)
				& (so_item.parent.isin(so_list))
				& (so_item.qty > so_item.work_order_qty)
				& (
					ExistsCriterion(
						frappe.qb.from_(bom)
						.select(bom.name)
						.where((bom.item == pi.item_code) & (bom.is_active == 1))
					)
				)
			)
		)

		if self.item_code:
			packed_items_query = packed_items_query.where(so_item.item_code == self.item_code)

		packed_items = packed_items_query.run(as_dict=True)

		self.add_items(items + packed_items)
		self.calculate_total_planned_qty()

	def calculate_total_planned_qty(self):
		self.total_planned_qty = 0
		for d in self.po_items:
			self.total_planned_qty += flt(d.planned_qty)

	def add_items(self, items):
		refs = {}
		for data in items:
			if not data.pending_qty:
				continue

			item_details = get_item_details(data.item_code, throw=False)
			if self.combine_items:
				bom_no = item_details.bom_no
				if data.get("bom_no"):
					bom_no = data.get("bom_no")

				if bom_no in refs:
					refs[bom_no]["so_details"].append(
						{"sales_order": data.parent, "sales_order_item": data.name, "qty": data.pending_qty}
					)
					refs[bom_no]["qty"] += data.pending_qty
					continue

				else:
					refs[bom_no] = {
						"qty": data.pending_qty,
						"po_item_ref": data.name,
						"so_details": [],
					}
					refs[bom_no]["so_details"].append(
						{"sales_order": data.parent, "sales_order_item": data.name, "qty": data.pending_qty}
					)

			bom_no = data.bom_no or item_details and item_details.get("bom_no") or ""
			if not bom_no:
				continue

			pi = self.append(
				"po_items",
				{
					"warehouse": data.warehouse,
					"item_code": data.item_code,
					"description": data.description or item_details.description,
					"stock_uom": item_details and item_details.stock_uom or "",
					"bom_no": bom_no,
					"planned_qty": data.pending_qty,
					"pending_qty": data.pending_qty,
					"planned_start_date": now_datetime(),
					"product_bundle_item": data.parent_item,
				},
			)
			pi._set_defaults()

			if self.get_items_from == "Sales Order":
				pi.sales_order = data.parent
				pi.project=frappe.db.get_value("Sales Order", data.parent, "project") or None
				pi.sales_order_item = data.name
				pi.description = data.description

			elif self.get_items_from == "Material Request":
				pi.material_request = data.parent
				pi.material_request_item = data.name
				pi.description = data.description

		if refs:
			for po_item in self.po_items:
				po_item.planned_qty = refs[po_item.bom_no]["qty"]
				po_item.pending_qty = refs[po_item.bom_no]["qty"]
				po_item.sales_order = ""
			self.add_pp_ref(refs)


	def add_pp_ref(self, refs):
		for bom_no in refs:
			for so_detail in refs[bom_no]["so_details"]:
				self.append(
					"prod_plan_references",
					{
						"item_reference": refs[bom_no]["po_item_ref"],
						"sales_order": so_detail["sales_order"],
						"sales_order_item": so_detail["sales_order_item"],
						"qty": so_detail["qty"],
					},
				)
	

	@frappe.whitelist()
	def get_open_sales_orders(self):
		"""Pull sales orders  which are pending to deliver based on criteria selected"""
		open_so = get_sales_orders(self)

		if open_so:
			self.add_so_in_table(open_so)
		else:
			frappe.msgprint(_("Sales orders are not available for production"))


	def add_so_in_table(self, open_so):
		"""Add sales orders in the table"""
		self.set("sales_orders", [])

		for data in open_so:
			self.append(
				"sales_orders",
				{
					"sales_order": data.name,
					"sales_order_date": data.transaction_date,
					"customer": data.customer,
					"grand_total": data.base_grand_total,
				},
			)
	
	@frappe.whitelist()
	def get_open_projects(self):
		"""Pull projects which are pending to deliver based on criteria selected"""
		project_list = get_projects(self)

		if project_list:
			self.add_project_in_table(project_list)
		else:
			frappe.msgprint(_("Projects are not available for production"))

	
	def get_project_items(self):
		bom = frappe.qb.DocType("BOM")
		ProjectPanels = frappe.qb.DocType("Project Panels")

		project_list=self.get_req_list("project", "project_details")


		bom_query = frappe.qb.from_(bom).select(bom.name).where(bom.is_active == 1)

		items_query = (
			frappe.qb.from_(ProjectPanels)
			.select(
				ProjectPanels.parent,
				ProjectPanels.item,
				ProjectPanels.qty,
				ProjectPanels.item_name

			)
			.distinct()
			.where(
					(ProjectPanels.parent.isin(project_list))
				)
			)
		
		project_items= items_query.run(as_dict=True)

		self.add_proj_item_in_table(project_items)	

	def add_proj_item_in_table(self, project_list):
		"""Add sales orders in the table"""
		self.set("po_items", [])

		for data in project_list:
			self.append(
				"po_items",
				{
					"item_code": data.item,
					"planned_qty": data.qty,
					"stock_uom": frappe.db.get_value("Item", data.item, "stock_uom"),
					"description": data.item_name,
					"planned_start_date": frappe.get_value('Project', data.parent, 'expected_start_date'),
					"project":data.parent,

				},
			)


	def add_project_in_table(self, project_list):
		"""Add sales orders in the table"""
		self.set("project_details", [])

		for data in project_list:
			self.append(
				"project_details",
				{
					"project": data.name,
					"expected_start": data.expected_start_date,
					"expected_end": data.expected_end_date,
				},
			)

	
	def get_req_list(self, field, table):
		"""Returns a list of Sales Orders or Material Requests from the respective tables"""
		req_list = [d.get(field) for d in self.get(table) if d.get(field)]
		return req_list

	def get_bom_item_condition(self):
		"""Check if Item or if its Template has a BOM."""
		bom_item_condition = None
		has_bom = frappe.db.exists({"doctype": "BOM", "item": self.item_code, "docstatus": 1})

		if not has_bom:
			bom = frappe.qb.DocType("BOM")
			template_item = frappe.db.get_value("Item", self.item_code, ["variant_of"])
			bom_item_condition = bom.item == template_item or None

		return bom_item_condition


def get_sales_orders(self):
	bom = frappe.qb.DocType("BOM")
	pi = frappe.qb.DocType("Packed Item")
	so = frappe.qb.DocType("Sales Order")
	so_item = frappe.qb.DocType("Sales Order Item")

	open_so_subquery1 = frappe.qb.from_(bom).select(bom.name).where(bom.is_active == 1)

	open_so_subquery2 = (
		frappe.qb.from_(pi)
		.select(pi.name)
		.where(
			(pi.parent == so.name)
			& (pi.parent_item == so_item.item_code)
			& (
				ExistsCriterion(
					frappe.qb.from_(bom)
					.select(bom.name)
					.where((bom.item == pi.item_code) & (bom.is_active == 1))
				)
			)
		)
	)

	open_so_query = (
		frappe.qb.from_(so)
		.from_(so_item)
		.select(so.name, so.transaction_date, so.customer, so.base_grand_total)
		.distinct()
		.where(
			(so_item.parent == so.name)
			& (so.docstatus == 1)
			& (so.status.notin(["Stopped", "Closed"]))
			& (so.company == self.company)
			& (so_item.qty > so_item.production_plan_qty)
		)
	)

	date_field_mapper = {
		"from_date": so.transaction_date >= self.from_date,
		"to_date": so.transaction_date <= self.to_date,
		"from_delivery_date": so_item.delivery_date >= self.from_delivery_date,
		"to_delivery_date": so_item.delivery_date <= self.to_delivery_date,
	}

	for field, value in date_field_mapper.items():
		if self.get(field):
			open_so_query = open_so_query.where(value)

	for field in ("customer", "project", "sales_order_status"):
		if self.get(field):
			so_field = "status" if field == "sales_order_status" else field
			open_so_query = open_so_query.where(so[so_field] == self.get(field))

	if self.item_code and frappe.db.exists("Item", self.item_code):
		open_so_query = open_so_query.where(so_item.item_code == self.item_code)
		open_so_subquery1 = open_so_subquery1.where(
			self.get_bom_item_condition() or bom.item == so_item.item_code
		)

	open_so_query = open_so_query.where(
		ExistsCriterion(open_so_subquery1) | ExistsCriterion(open_so_subquery2)
	)

	open_so = open_so_query.run(as_dict=True)

	return open_so



def get_projects(self):
	from frappe.query_builder import DocType

	Project = DocType("Project")
	ProjectPanels = DocType("Project Panels")

	query = (
		frappe.qb.from_(Project)
		.select(Project.name, Project.expected_start_date, Project.expected_end_date)
		.where(Project.company == self.company)
		.orderby(Project.expected_start_date)
	)

	# Optional filters
	if self.project:
		query = query.where(Project.name == self.project)

	if self.from_date:
		query = query.where(Project.expected_start_date >= self.from_date)

	if self.to_date:
		query = query.where(Project.expected_start_date <= self.to_date)

	# If filtering by item_code, ensure the project has that item in its Project Panels child table
	if self.item_code and frappe.db.exists("Item", self.item_code):
		subquery = (
			frappe.qb.from_(ProjectPanels)
			.select(ProjectPanels.parent)
			.where(
				(ProjectPanels.parent == Project.name) &
				(ProjectPanels.item == self.item_code)
			)
		)
		query = query.where(ExistsCriterion(subquery))

	projects = query.run(as_dict=True)
	return projects
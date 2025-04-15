# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExpectedSales(Document):
	
	def validate(self):
		self.check_for_duplicate_item_codes()
		self.validate_expected_date()
		
	def validate_expected_date(self):
		if self.expected_end<self.expected_date:
			frappe.throw("Please make sure that the Expected End is bigger")
    
	def check_for_duplicate_item_codes(self):
		item_codes = []
		for item in self.item_records:
			if item.item_code in item_codes:
				frappe.msgprint(f"The item code {item.item_code} is already in the list at row {item.idx}.")
			else:
				item_codes.append(item.item_code)
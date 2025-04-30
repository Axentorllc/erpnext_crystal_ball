# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime

class ExpectedSales(Document):
	
	def autoname(self):
		"""Generates the name of the document based for type "Committed"."""

		if self.type =="Committed":
			if isinstance(self.expected_date, str):
				expected_start = datetime.strptime(self.expected_date, "%Y-%m-%d").date()
			else:
				expected_start = self.expected_date

			week_num=self.get_week_number(expected_start)
			self.name = f"Committed-{self.month}-{self.fiscal_year}-week {week_num}"

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

	def get_week_number(self,date_obj):
		"""Returns the week number of a given date in its month (Fixed 5 weeks)."""
		return (date_obj.day - 1) // 7 + 1
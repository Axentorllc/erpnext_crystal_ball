# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class ProjectedBudget(Document):
    
    def validate(self):
        # Replace 'start_date' and 'end_date' with the field names you want to validate
        self.validate_from_to_dates('start_date', 'end_date')
       

   

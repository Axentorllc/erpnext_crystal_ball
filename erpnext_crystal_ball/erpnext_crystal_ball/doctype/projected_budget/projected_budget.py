# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document       
from datetime import datetime
class ProjectedBudget(Document):
    
    def validate(self):
        # Replace 'start_date' and 'end_date' with the field names you want to validate
        self.validate_from_to_dates('start_date', 'end_date')
        self.before_save_naming()
    

    def before_save_naming(self):

        if self.start_date and self.fiscal_year:
            month_name = datetime.strptime(self.start_date, '%Y-%m-%d').strftime('%B')
            
            self.name = f"PB-{self.fiscal_year}-{month_name[:3]}"
   

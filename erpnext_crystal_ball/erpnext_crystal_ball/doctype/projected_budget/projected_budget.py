# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document       
from datetime import datetime
class ProjectedBudget(Document):
    
    def validate(self):
        self.validate_from_to_dates('start_date', 'end_date')
        self.before_save_naming()
        self.check_for_duplicate_accounts()
    

    def before_save_naming(self):

        if self.start_date and self.fiscal_year:
            month_name = datetime.strptime(self.start_date, '%Y-%m-%d').strftime('%B')
            
            self.name = f"PB-{self.fiscal_year}-{month_name[:3]}"
   
    def check_for_duplicate_accounts(self):

        account_list=[]
        for row in self.accounts:
            account=row.account
            if account in account_list:
                frappe.msgprint(f"The account {account} is already exists at raw{row.idx} .")

            else:
                account_list.append(account)

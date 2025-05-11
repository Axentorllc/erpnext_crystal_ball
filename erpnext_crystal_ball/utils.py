# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
import datetime
from datetime import datetime ,timedelta
from dateutil.relativedelta import relativedelta

def get_months_range(from_date_str,to_date_str):

		"""Generate a list of month names between the given date range."""

		from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
		to_date = datetime.strptime(to_date_str, '%Y-%m-%d')

		months=[]
		current_date=from_date
		while current_date <= to_date:
			month_name= current_date.strftime('%B')
			if month_name not in months:
				months.append(month_name)
			current_date += relativedelta(months=1)
		
		return months

def get_week_number(date_obj):
    """Returns the week number of a given date in its month (Fixed 5 weeks)."""
    return (date_obj.day - 1) // 7 + 1


def get_fg_stock_qty(item_code):
	"""
    Fetches the available quantity for a given finished goods item.
	"""

	fg_stock_qty=0
	bin_data=frappe.get_list('Bin',
					filters={'item_code':item_code},fields=['actual_qty'])
	
	for raw in bin_data:
		fg_stock_qty+=raw.get('actual_qty')

	return fg_stock_qty

@frappe.whitelist()
def get_item_expected_time(routing):
	"""
	fetches the expected time for a given item based on its routing.
	""""""
	Calculate the total expected manufacturing time for an item 
	based on its associated Routing operations.

	Args:
		routing (str): The name of the Routing document.

	Returns:
		float: Total time in minutes required to complete all operations.
	"""
	
	routing_doc=frappe.get_doc('Routing',routing)

	expected_time=0

	# Loop through each operation in the Routing document
	for operation in routing_doc.operations:
		expected_time+=operation.time_in_mins or 0

	return expected_time
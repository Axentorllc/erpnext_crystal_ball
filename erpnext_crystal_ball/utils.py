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
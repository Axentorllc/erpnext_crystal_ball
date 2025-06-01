# Copyright (c) 2025, Carlos and contributors
# For license information, please see license.txt

from datetime import datetime, timedelta ,time
import frappe
from frappe.model.document import Document
import math
import frappe
import json
import string

class CapacitySlot(Document):
	pass


BUFFER_MINUTES = 10  # e.g., 10 mins buffer before and after slots

def slots_overlap(start1, end1, start2, end2, buffer_minutes=BUFFER_MINUTES):
    buffer = timedelta(minutes=buffer_minutes)
    return (start1 - buffer) < (end2 + buffer) and (end1 + buffer) > (start2 - buffer)


def get_existing_capacity_slots(start_date, end_date):
    return frappe.get_all('Capacity Slot',
        filters=[
            ['expected_end', '>=', start_date],
            ['expected_start', '<=', end_date]
        ],
        fields=[
            'workstation', 'production_team', 'operation_start', 'operation_end'
        ]
    )


def build_existing_availability_map(existing_slots):
    workstation_map = {}
    team_map = {}

    for slot in existing_slots:
        # For workstations
        workstation_map.setdefault(slot['workstation'], []).append({
            'start_time': slot['operation_start'],
            'end_time': slot['operation_end']
        })

        # For teams
        if slot['production_team']:
            team_map.setdefault(slot['production_team'], []).append({
                'start_time': slot['operation_start'],
                'end_time': slot['operation_end']
            })

    return workstation_map, team_map



def is_team_available(team, start_time, end_time, operation_team_map):
    """
    Check if the given team is available during the specified time window.
    Logs busy status for conflict.
    """
    if team not in operation_team_map["availability"]:
        return True

    for existing_slot in operation_team_map["availability"][team]:
        if (
            start_time < existing_slot["end_time"]
            and end_time > existing_slot["start_time"]
        ):
            # Team is busy during this time
            operation_team_map["status"][team] = f"Busy on {existing_slot['workstation']} from {existing_slot['start_time']} to {existing_slot['end_time']}"
            return False
    return True



def initialize_workstation_structure():
	ws_list = frappe.get_list("Workstation", fields=["name", "custom_dimensions"])
	ws_structure = {}
	
	for ws in ws_list:
		ws_structure[ws.name] = {
			"area":  f"Area {ws.custom_dimensions}",
			"dimension": ws.custom_dimensions,
			"project": None,
			"start_date": None,
			"end_date": None,
			"items":[]
		}
	
	return ws_structure


def categorize_workstations_by_dimension():
	workstations = frappe.get_list("Workstation", fields=["name", "custom_dimensions"])
	
	# Create dimension-wise grouping
	from collections import defaultdict
	dimension_groups = defaultdict(list)
	
	for ws in workstations:
		dimension_groups[ws.custom_dimensions].append(ws.name)
		
	
	# Assign area letters
	production_area_data = []
	for idx, dimension in enumerate(sorted(dimension_groups)):
		production_area_data.append({
			"area": f"Area {dimension}",
			"dimension": dimension,
			"total_workstation_qty": len(dimension_groups[dimension]),
			"available_workstation_qty": len(dimension_groups[dimension]),
			"workstations": dimension_groups[dimension],   # how to update the avialble ws names
		})

	return production_area_data


def is_workstation_available(ws, start_time, end_time, existing_ws_map, current_ws_schedule):
    # Check existing assignments in db
    for slot in existing_ws_map.get(ws, []):
        if start_time < slot['end_time'] and end_time > slot['start_time']:
            return False

    # Check current assignments in-memory (ws_schedule) if needed
    for assigned_slot in current_ws_schedule.get(ws, {}).get("items", []):
        for op in assigned_slot.get("operations", []):
            if start_time < op["end_time"] and end_time > op["start_time"]:
                return False

    return True


def get_production_team_map_by_operation():
    """
    Builds and returns a mapping of operations to production teams.

    Returns:
        dict: {
            operation_name: {
                "teams": [team_1, team_2, ...],
                "status": {
                    team_1: "unassigned" or "Busy on {workstation} from {start_time} to {end_time}",
                    ...
                },
                "availability": {
                    team_1: [
                        {
                            "start_time": datetime,
                            "end_time": datetime,
                            "workstation": str,
                            "item": str,
                            "operation": str
                        },
                        ...
                    ],
                    ...
                }
            },
            ...
        }
    """
    production_team_map = {}

    team_names = frappe.get_list("Production Team", pluck="name")
    for team_name in team_names:
        team_doc = frappe.get_doc("Production Team", team_name)
        for operation_row in team_doc.operation:
            operation_name = operation_row.operation

            entry = production_team_map.setdefault(
                operation_name,
                {
                    "teams": [],
                    "status": {},
                    "availability": {}
                }
            )

            if team_name not in entry["teams"]:
                entry["teams"].append(team_name)

            entry["status"][team_name] = "unassigned"
            entry["availability"][team_name] = []

    return production_team_map



def get_no_ws(item_details):
	"""
    Calculates project-wise workstation needs based on total dimension.
    Uses collected project data for items and project meta.
    """
	import math

	project_details = {}
	ws_category = categorize_workstations_by_dimension()

	# Sort workstations by available qty descending, prioritize bigger dimension
	ws_category.sort(key=lambda x: (-x["available_workstation_qty"], -x["dimension"]))


	for item_code, item_info in item_details.items():
		total_dimension = 0

		if item_info and item_info.get('dimension'):
			total_dimension += float(item_info.get('dimension')) * float(item_info.get('qty'))


		# Now find the suitable area with available workstations
		for area in ws_category:
			area_dim = area["dimension"]
			available_ws = area["available_workstation_qty"]
			if area_dim > 0:
				num_ws_needed = math.ceil(total_dimension / area_dim)
				if num_ws_needed <= available_ws:
					project_details[item_info.get('project')] = {
						'expected_start_date': item_info.get('project_info').get('expected_start'),
						'expected_end_date': item_info.get('project_info').get('expected_end'),
						'num_ws_needed': num_ws_needed,
						'workstation_dimension': area_dim,
						'picked_workstations': area["workstations"][:num_ws_needed],
						'area': area["area"],
					}
					# Optionally update availability if needed
					area["available_workstation_qty"] -= num_ws_needed

					break  # stop looking further once assigned

	return project_details


def get_workstation_hours(ws):
    ws_doc = frappe.get_doc('Workstation', ws)
    if ws_doc.working_hours:
        ws_h = ws_doc.working_hours[0]
        return ws_h.start_time, ws_doc.end_time
    else:
        return time(8, 0, 0), time(16, 0, 0)  # Default hours


def parse_project_dates(project_info):
    start_str = project_info.get('expected_start')
    end_str = project_info.get('expected_end')
    start_date = datetime.strptime(start_str, '%Y-%m-%d') if start_str else None
    end_date = datetime.strptime(end_str, '%Y-%m-%d') if end_str else None
    return start_date, end_date


def assign_team_to_operation(operation_name, operation_team_map, current_start_time, ws, item_code):
    teams_info = operation_team_map.get(operation_name, {"teams": [], "status": {}, "availability": {}})
    assigned_team = None
    operation_end_time = None

    for team in teams_info["teams"]:
        status = teams_info["status"].get(team, "unassigned")
        if status == "unassigned":
            assigned_team = team
            break
        # Could add availability conflict checks here

    if assigned_team:
        # Assign operation time (dummy duration, will be set later)
        # But here we don't have operation_time, so we'll set it after call
        pass

    return assigned_team, teams_info


def process_item_operations(item_detail, operation_team_map, ws, ws_start_datetime, item_code):
    operations = []
    current_start_time = ws_start_datetime

    for op in item_detail.get("operations", []):
        operation_name = op["operation"]
        operation_time = op["operation_time"]

        assigned_team, teams_info = assign_team_to_operation(
            operation_name, operation_team_map, current_start_time, ws, item_code
        )

        operation_end_time = current_start_time + timedelta(minutes=operation_time)

        if assigned_team:
            teams_info["status"][assigned_team] = (
                f"Busy on {ws} from {current_start_time.strftime('%Y-%m-%d %H:%M')} "
                f"to {operation_end_time.strftime('%Y-%m-%d %H:%M')}"
            )
            teams_info["availability"].setdefault(assigned_team, []).append({
                "start_time": current_start_time,
                "end_time": operation_end_time,
                "workstation": ws,
                "item": item_code,
                "operation": operation_name
            })

        operations.append({
            "operation": operation_name,
            "operation_time": operation_time,
            "team": assigned_team,
            "start_time": current_start_time,
            "end_time": operation_end_time,
        })

        current_start_time = operation_end_time

    return operations


def assign_items_to_workstations(item_details):
	ws_schedule = initialize_workstation_structure()
	
	# item_details=get_item_details(project_list)
	ws_req_details=get_no_ws(item_details)

	operation_team_map= get_production_team_map_by_operation()
  
	# convert the dict into list of tuples to be easily get idx
	item_list= list(item_details.items()) 

	#  use enumerate to get the index of the item
	for idx ,(item_code, item_detail) in enumerate(item_list):
		project_name = item_detail["project"]
		picked_workstations = ws_req_details.get(project_name, {}).get('picked_workstations', [])
		num_ws=len(picked_workstations) 

		if num_ws == 0:
			continue

		# assgin items according to dim may the ws can hold to items together an lets keep the items with the same route together
		ws=picked_workstations[idx % num_ws]  # Round-robin assignment of workstations 

		ws_start_time, ws_end_time = get_workstation_hours(ws)

		proj_info=item_detail.get('project_info', {})
		start_date, end_date = parse_project_dates(proj_info)

		ws_start_datetime = datetime.combine(start_date, ws_start_time) if start_date else None
		ws_end_datetime = datetime.combine(end_date, ws_end_time) if end_date else None

		if ws in ws_schedule:
			ws_schedule[ws]['area'] = ws_req_details.get(project_name).get('area')
			ws_schedule[ws]['dimension'] = ws_req_details.get(project_name).get('workstation_dimension')
			ws_schedule[ws]['start_date'] = ws_start_datetime
			ws_schedule[ws]['end_date'] = ws_end_datetime


		operations = process_item_operations(item_detail, operation_team_map, ws, ws_start_datetime, item_code)
				
		ws_schedule[ws]["items"].append({
		"item_code": item_code,
		"project": item_detail["project"],
		"qty": item_detail["qty"],
		"dimension": item_detail["dimension"],
		"expected_time": item_detail["expected_time"],
		"route": item_detail["route"],
		"operations": operations
		})

	print("after",operation_team_map)
	return ws_schedule



@frappe.whitelist()
def update_capacity_slot(item_details):
	"""Create a Capacity Slot document for each item-operation pair within the given project date range."""


	ws_structure = assign_items_to_workstations(item_details)

	for ws_name, ws_details in ws_structure.items():
		base_fields = {
			"doctype": "Capacity Slot",
			"workstation": ws_name,
			"ws_dimension": ws_details.get("dimension"),
			"expected_start": ws_details.get("start_date"),
			"expected_end": ws_details.get("end_date"),
		}
		
		if ws_details["items"]:
			for item in ws_details["items"]:
				for op in item.get("operations", []):
					doc = frappe.get_doc({
						**base_fields,
						"item": item["item_code"],
						"project": item["project"],
						"item_qty": item["qty"],
						"item_dimension": item["dimension"],
						"expected_time": item["expected_time"],
						"operation": op["operation"],
						"operation_time": op["operation_time"],
						"operation_start": op["start_time"],
						"operation_end": op["end_time"],
						"production_team": op["team"]
					})
					doc.insert()

		else:
			frappe.get_doc(base_fields).insert()


		frappe.db.commit()



@frappe.whitelist()
def create_capacity_slots(items, project_details):

	item_details={}

	item_list = json.loads(items)
	project_list = json.loads(project_details)


	project_info = {
        proj['project']: {
            'expected_start': proj['expected_start'],
            'expected_end': proj['expected_end']
        }

		if proj.get('expected_start') and proj.get('expected_end')
		else {'expected_start': None, 'expected_end': None}
        for proj in project_list
    }

	for row in item_list:

		# Fetch item master to get dimension, custom_route, expected_time
		item = frappe.get_doc('Item', row['item_code'])

		# Gather all operations for this item
		operations = []
		if item.get('custom_route'):
			routing_doc = frappe.get_doc("Routing",item.get('custom_route'))
			for op in routing_doc.operations:
				operations.append({
					"operation": op.operation,
					"operation_time": op.time_in_mins,
				})

		# Build your dict
		item_details[row['item_code']] = {
			'project':       row['project'],
			'qty':           row['planned_qty'],
			'dimension':     item.get('custom_dimensions'),
			'route':  item.get('custom_route'),
			'expected_time': item.get('custom_expected_time'),
			'project_info': project_info.get(row['project']),
			'operations':    operations
		}

	project_workstations = {}

	# update_capacity_slot(item_details)
	print(item_details)

	# for proj in project_info.keys():
	# 	project_items = {k: v for k, v in item_details.items() if v['project'] == proj}
	# 	print(project_items)
		# project_workstations[proj] = calculate_workstations(project_items)

	# At this point `result` is a list of dicts in your desired format.
	# You can return it, or loop on it to create Capacity Slot records, etc.
	# print (item_details)

	# return item_details



# def num_of_ws_needed(project_items):
# 	ws_category = categorize_workstations_by_dimension()

# 	total_dimension = 0.0

# 	for item_code , item_info in project_items.items():
# 		if item_info and item_info.get('dimension'):
# 			total_dimension += float(item_info.get('dimension')) * float(item_info.get('qty'))

# 	for area in ws_category:
# 		if area['dimension'] > 0:
# 			pass

# import math
# from collections import defaultdict
# from datetime import datetime

# def assign_workstations_and_reserve(item_details):
# 	"""
# 	Assign workstations to projects based on item dimensions and reserve them by project schedules.

# 	Parameters:
# 	- item_details: dict of items with info including 'project', 'qty', 'dimension', 'project_info' (contains 'expected_start' and 'expected_end')
# 	- ws_data: list of dicts describing workstations availability and dimension info

# 	Returns:
# 	- project_assignments: dict mapping project -> {
# 		'needed_workstations': int,
# 		'assigned_workstations': list of workstation names assigned,
# 		'item_to_workstation': dict mapping item_code -> workstation name,
# 		'workstation_reservations': dict mapping workstation -> list of reserved (start_date, end_date)
# 	}
# 	- updated_ws_data: ws_data with updated 'available_workstation_qty' after reservations
# 	"""

# 	ws_data=categorize_workstations_by_dimension()

# 	# Prepare a flat list of all available workstations with their dimension and link to ws_data for updates
# 	available_ws = []
# 	for area in ws_data:
# 		for ws_name in area['workstations']:
# 			available_ws.append({
# 				'name': ws_name,
# 				'dimension': area['dimension'],
# 				'area_ref': area
# 			})
# 	# Sort workstations by dimension ascending to assign smallest fitting WS first
# 	available_ws.sort(key=lambda ws: ws['dimension'])

# 	# Track which workstations are reserved and their reserved periods
# 	# Format: { ws_name: [(start_datetime, end_datetime), ...] }
# 	workstation_reservations = defaultdict(list)

# 	# Group items by project for batch processing
# 	projects = defaultdict(list)
# 	for item_code, info in item_details.items():
# 		projects[info['project']].append((item_code, info))

# 	project_assignments = {}

# 	for project, items in projects.items():
# 		# Calculate total dimension demand for the project (qty * dimension for each item)
# 		total_dim_required = 0.0
# 		for item_code, info in items:
# 			dim = info.get('dimension')
# 			qty = info.get('qty', 1)
# 			if dim:  # skip None or zero dimensions
# 				total_dim_required += dim * qty

# 		# Extract project schedule (expecting all items have same expected_start/end)
# 		proj_info = items[0][1].get('project_info', {}) if items else {}
# 		start_str = proj_info.get('expected_start')
# 		end_str = proj_info.get('expected_end')
# 		start_date = datetime.strptime(start_str, '%Y-%m-%d') if start_str else None
# 		end_date = datetime.strptime(end_str, '%Y-%m-%d') if end_str else None

# 		assigned_workstations = []
# 		assigned_ws_indices = set()
# 		total_capacity = 0.0

# 		# Assign WS until capacity meets or exceeds needed dimension
# 		for idx, ws in enumerate(available_ws):
# 			if is_workstation_free(ws['name'], workstation_reservations, start_date, end_date):
# 				assigned_workstations.append(ws['name'])
# 				assigned_ws_indices.add(idx)
# 				total_capacity += ws['dimension']
# 				if total_capacity >= total_dim_required:
# 					break

# 		# Map each item round-robin to assigned WS
# 		item_to_ws = {}
# 		num_ws = len(assigned_workstations)
# 		for i, (item_code, _) in enumerate(items):
# 			if num_ws > 0:
# 				item_to_ws[item_code] = assigned_workstations[i % num_ws]
# 			else:
# 				item_to_ws[item_code] = None  # no WS available

# 		# Register reservation periods for assigned WS
# 		for ws_name in assigned_workstations:
# 			if start_date and end_date:
# 				workstation_reservations[ws_name].append((start_date, end_date))
# 			# Update available quantity in ws_data:
# 			for area in ws_data:
# 				if ws_name in area['workstations']:
# 					area['available_workstation_qty'] = max(area['available_workstation_qty'] - 1, 0)

# 		# Remove reserved WS from available pool to prevent double assignment in next projects
# 		available_ws = [ws for idx, ws in enumerate(available_ws) if idx not in assigned_ws_indices]

# 		project_assignments[project] = {
# 			'needed_workstations': len(assigned_workstations),
# 			'assigned_workstations': assigned_workstations,
# 			'item_to_workstation': item_to_ws,
# 			'workstation_reservations': {ws: workstation_reservations[ws] for ws in assigned_workstations}
# 		}

# 	print( project_assignments, ws_data)

# def is_workstation_free(ws_name, reservations, start_date, end_date):
#     """
#     Checks if the ws_name is free (not reserved) during [start_date, end_date].

#     Returns True if free, False if there is an overlap with existing reservations.
#     """
#     if ws_name not in reservations:
#         return True
#     for (res_start, res_end) in reservations[ws_name]:
#         # Check if periods overlap
#         if start_date <= res_end and end_date >= res_start:
#             return False
#     return True


# # Example usage:
# if __name__ == "__main__":
#     ws_data_example = [
#         {'area': 'Area 0.0', 'dimension': 0.0, 'total_workstation_qty': 1, 'available_workstation_qty': 1, 'workstations': ['Production Floor']},
#         {'area': 'Area 180.0', 'dimension': 180.0, 'total_workstation_qty': 3, 'available_workstation_qty': 3, 'workstations': ['Table-2', 'Table-3', 'Table-1']},
#         {'area': 'Area 430.0', 'dimension': 430.0, 'total_workstation_qty': 2, 'available_workstation_qty': 2, 'workstations': ['Table-4', 'Table-5']}
#     ]

#     project_items_example = {
#         'ITM-ABB-PNL-28642': {
#             'project': 'PROJ-2042',
#             'qty': 1,
#             'dimension': 30.0,
#             'project_info': {'expected_start': '2025-05-01', 'expected_end': '2025-05-15'}
#         },
#         'ITM-ABB-PNL-30579': {
#             'project': 'PROJ-2042',
#             'qty': 1,
#             'dimension': 180.0,
#             'project_info': {'expected_start': '2025-05-01', 'expected_end': '2025-05-15'}
#         }
#     }

#     assignments, updated_ws = assign_workstations_and_reserve(project_items_example, ws_data_example)
#     import pprint
#     pprint.pprint(assignments)
#     pprint.pprint(updated_ws)





	



""" """


"""
item_code={
	"qty": qty
	"project": project_name,
	"dimension": get from Item 'dimension',
	"custom_route": get from Item 'custom_route',
	"expected_time": get from Item 'expected_time',
	"operations": [
		{
			"operation": "operation_name",
			"operation_time": operation_time
		},
		...
	]
[{'item_code': 'ITM-ABB-PNL-28642', 'qty': 1, 'project': 'PROJ-2042', 'dimension': None, 'custom_route': 'X-P-0-0', 'expected_time': None, 'project_info': {'expected_start': '2025-05-01', 'expected_end': '2025-05-15'}, 'operations': [{'operation': 'Panel Weilding', 'operation_time': 30.0}, {'operation': 'Panel Building', 'operation_time': 60.0}]}
}
"""




"""

workstation_schedule = {
    'W.S 1': {
        'area': 'A',
        'dimension': 180,
        'start_date': 'according to the project' + time of start of project, '01-06-2025' + 8:00:00
        'end_date': start_date + expected_time of all items asgined to it,',
        'Item-01': {
				'project': 'Project-01',
                'qty': 1.0,
                'dimension': 30.0,
                'expected_time': 90.0,
                'route': 'X-P-0-0',
                # You have to assign a team for each operation
                'operation': 
                    {
					    
                        'team': 'Team A',
                        'operation': 'operation A',
                        'operation_time': 30.0
						'start_time': project start date
						'end_time': start_time + operation_time
                    },
					}
                    'operation':{
                        'team': 'Team B',
                        'operation': 'operation B',
                        'operation_time': 60.0
						'start_time': end of priv operation
						'end_time': start_time + operation_time
                    }
                ]
            }
        }
    },
    'W.S 2': {
        'area': 'A',
        'dimension': 80,
        'project': 'Project-01',
        'start_date': 'according to the project',
        'end_date': 'according to the project',
        'item': {
            'Item-02': {
                'qty': 1.0,
                'dimension': 30.0,
                'expected_time': 90.0,
                'route': 'X-P-0-0',
                # You have to assign a team for each operation
                'operations': [
                    {
                        'team': 'Team A',
                        'operation': 'operation A',
                        'operation_time': 30.0
                    },
                    {
                        'team': 'Team B',
                        'operation': 'operation B',
                        'operation_time': 60.0
                    }
                ]
            }
        }
    }
}

"""


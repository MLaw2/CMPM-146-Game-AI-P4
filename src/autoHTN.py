import pyhop
import json

def check_enough (state, ID, item, num):
	if getattr(state,item)[ID] >= num: return []
	return False

def produce_enough (state, ID, item, num):
	return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods ('have_enough', check_enough, produce_enough)

def produce (state, ID, item):
	return [('produce_{}'.format(item), ID)]

pyhop.declare_methods ('produce', produce)

def make_method (name, rule):
	def method (state, ID):
		# your code here
		final = []
		item = list(rule["Produces"].keys())[0]
		number = rule["Produces"][item]
		for category in rule.keys():
			if category == "Requires" or category == "Consumes":
				final.append(('have_enough', ID, item, number))
		# fix operator string
		operator = "op_" + name
		operator = operator.replace(' ', '_')
		final.append((operator, ID))
		return final
		pass
	# producedItem = list(rule['Produces'].keys())
	method.__name__ = name
	return method

### TODO
# # DOES NOT SORT PROPER. PLS FIX
def sort_methods(methodList, data):
	sortedMethods = {}
	for method in methodList:
		recipeName = method.__name__
		producedItem = list(data["Recipes"][recipeName]["Produces"].keys())[0]
		methodNames = list(sortedMethods.keys())
		if methodNames.count(producedItem) == 0:
			sortedMethods.update({producedItem: [method]})
		else: #this means that producedItem is most likely coal, wood, or ore
			#time to sort
			if method.__name__.find("iron")>=0:
				sortedMethods.update({producedItem: [method] + sortedMethods[producedItem]})
			elif method.__name__.find("stone")>=0:
				temp = sortedMethods[producedItem]
				if temp[0].__name__.find('iron')>=0:
					temp.insert(1, method)
				else:
					temp.insert(0, method)
				sortedMethods.update({producedItem: temp})
			elif method.__name__.find("wooden")>=0:
				temp = sortedMethods[producedItem]
				if temp[-1].__name__.find("punch") >= 0:
					temp.insert(len(temp)-1, method)
				else:
					temp.append(method)
				sortedMethods.update({producedItem: temp})
			elif method.__name__.find("punch")>=0:
				#this should be punch (right?)
				sortedMethods.update({producedItem: sortedMethods[producedItem] + [method]})
			else:
				print("THAT WASN'T SUPPOSED TO HAPPEN")
	return sortedMethods

def declare_methods (data):
	# some recipes are faster than others for the same product even though they might require extra tools
	# sort the recipes so that faster recipes go first

	# your code here


	### TODO
	# I gotta redo declare methods
	# New approach: First make the methods from the Recipes
	# Then: Sort the methods into common items(all the cobble methods go in one place)
	methodList = []
	for recipeName in data["Recipes"].keys():
		rules = data["Recipes"][recipeName]
		method = make_method(recipeName, rules)
		methodList.append(method)
	# now I need to sort the methods by the item
	# CREATE A SORTING METHOD THAT RETURNS A DICT OF ITEMS AND VALUES
	sortedMethods = sort_methods(methodList, data)
	# time to declare all the methods
	for item, temp in sortedMethods.items():
		temp = []
		for method in sortedMethods[item]:
			#replace spaces with underscores
			method.__name__ = method.__name__.replace(' ', '_')
			temp.append(method)
		pyhop.declare_methods("produce_" + item, *temp)

	# hint: call make_method, then declare the method to pyhop using pyhop.declare_methods('foo', m1, m2, ..., mk)	
	# pyhop.print_methods()
	pass

def make_operator (rule):
	def operator (state, ID):
		# your code here
		for key, value in rule.items():
			if key == 'Produces':
				for item, num in  value.items():
					setattr(state, item, {ID: getattr(state, item)[ID] + num})
			if key == 'Time':
				if state.time[ID] >= num:
					state.time[ID] -= num
				else:
					return False
			if key == 'Consumes':
				for item, num in value.items():
					if getattr(state, item)[ID] >= num:
						setattr(state, item, {ID: getattr(state, item)[ID] - num})
		return state
	return operator

def declare_operators (data):
	# your code here
	# hint: call make_operator, then declare the operator to pyhop using pyhop.declare_operators(o1, o2, ..., ok)
	op_list = []
	for key, value in sorted(data['Recipes'].items(), key=lambda item: item[1]["Time"], reverse=True):
		key = key.replace(" ", "_")
		time_for_this = value['Time']
		temp = make_operator(value)
		temp.__name__ = 'op_' + key
		op_list.append((temp, time_for_this))
		sorted(op_list, key=lambda item: time_for_this, reverse=False)
	for cur, _ in op_list:
		pyhop.declare_operators(cur)

def add_heuristic (data, ID):
	# prune search branch if heuristic() returns True
	# do not change parameters to heuristic(), but can add more heuristic functions with the same parameters: 
	# e.g. def heuristic2(...); pyhop.add_check(heuristic2)
	def heuristic (state, curr_task, tasks, plan, depth, calling_stack):
		if curr_task in tasks:
			return False
		return True
	
	def heuristic2 (state, curr_task, tasks, plan, depth, calling_stack):
		return depth > 500
		# if True, prune this branch

	pyhop.add_check(heuristic)
	pyhop.add_check(heuristic2)


def set_up_state (data, ID, time=0):
	state = pyhop.State('state')
	state.time = {ID: time}

	for item in data['Items']:
		setattr(state, item, {ID: 0})

	for item in data['Tools']:
		setattr(state, item, {ID: 0})

	for item, num in data['Initial'].items():
		setattr(state, item, {ID: num})

	return state

def set_up_goals (data, ID):
	goals = []
	for item, num in data['Goal'].items():
		goals.append(('have_enough', ID, item, num))

	return goals

if __name__ == '__main__':
	rules_filename = 'crafting.json'

	with open(rules_filename) as f:
		data = json.load(f)

	state = set_up_state(data, 'agent', time=239) # allot time here
	goals = set_up_goals(data, 'agent')

	declare_operators(data)
	declare_methods(data)
	add_heuristic(data, 'agent')

	pyhop.print_operators()
	pyhop.print_methods()

	# Hint: verbose output can take a long time even if the solution is correct; 
	# try verbose=1 if it is taking too long
	pyhop.pyhop(state, goals, verbose=1)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)

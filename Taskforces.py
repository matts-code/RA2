from collections import Counter
import configparser
import random


class Taskforce(object):
	"""Creates and analyzes Taskforce objects for the game Red Alert 2"""

	num_tfs = 0
	used_ids = []
	live_units = {}

	def __init__(self, unit_ids=None, tfid=None, name=None, group=None):
		self.units = unit_ids
		self.name = name
		self.group = group

		Taskforce.num_tfs += 1

		#need to make sure ids are unique
		if tfid == None:
			self.tfid = 'tf{}'.format(Taskforce.num_tfs)
		else:
			self.tfid = tfid

		Taskforce.used_ids.append(tfid)

	@property
	def units(self):
		"""Returns the actual unit data when accessing by units attribute."""
		return [Taskforce.live_units[unit] for unit in self.unit_ids]

	@units.setter
	def units(self, unit_ids):
		"""Allows creating taskforce from list of unit ids."""
		if unit_ids is None:
			unit_ids = []
		self.unit_ids = unit_ids

	def side(self):
		"""Returns the most likely side for the taskforce"""
		if self.same_side():
			return Counter(unit['Side'] for unit in self.units).most_common(1)[0][0]
		else:
			return 'Multi'

	def __len__(self):
		return len(self.units)

	def __eq__(self, other): #should order matter for equality?
		pass

	def reorder(self, key='Passengers'):
		"""Reorders units in taskforce, high to low, based on key"""
		s = sorted(self.units, key=lambda unit: unit[key], reverse=True)
		self.unit_ids = [unit['UnitID'] for unit in s]

	def loadable(self):
		if len(self.units) < 2:
			return False
		#could be handled better

		self.reorder('Passengers')

		total_space = self.units[0]['Passengers']
		enough_space = total_space >= sum(unit['Size'] for unit in self.units[1:])

		max_size = self.units[0]['SizeLimit']
		largest_unit = max(self.units[1:], key=lambda unit: unit['Size'])['Size']
		all_fit = max_size >= largest_unit

		can_load = enough_space and all_fit
		return can_load

	def add_transport(self):
		#try to avoid hardcoding the transport ids
		pass

	def add_units(self, unit_ids):
		"""Adds units from unit_ids to taskforce."""
		self.unit_ids.extend(unit_ids)

	def __add__(self, other):
		unit_ids = self.unit_ids + other.unit_ids
		#name = '{}+{}'.format(self.tfid, other.tfid)
		return Taskforce(unit_ids)

	def remove_units(self, unit_ids):
		"""Removes unit_ids from the taskforce."""
		#possibly use Counters
		pass

	def __sub__(self, other):
		"""Removes other taskforces units from self if present."""
		#possibly use Counters
		pass

	def total_cost(self):
		total = sum(unit['Cost'] for unit in self.units)
		return total

	def total_size(self):
		return sum(unit['Size'] for unit in self.units)

	def counts(self):
		return Counter(unit['Name'] for unit in self.units)

	def can_take(self, other):
		"""Can this team accept all units from other in a Change Team script action?"""
		tf1 = Counter(self.unit_ids)
		tf2 = Counter(other.unit_ids)
		tf1.subtract(tf2)
		result = all(count >= 0 for count in tf1.values())
		return result

	def all_inf(self):
		#are all units infantry
		return all(unit['Category'] == 'Soldier' for unit in self.units)

	def all_land(self):
		#are all units land based
		#maybe use movementzone
		pass

	def all_air(self):
		#are all units aircraft
		return all(unit['ConsideredAircraft'] for unit in self.units)

	def all_naval(self):
		#are all units naval
		return all(unit['Naval'] for unit in self.units)

	def all_subs(self):
		#are all units underwater
		return all(unit['Underwater'] for unit in self.units)

	def no_attack(self):
		#can none of the units attack anything
		pass

	def can_ally(self, other):
		#can both teams move with coordinated movement
		#order maybe matters
		pass

	def n_uniques(self):
		return len(set(self.unit_ids))

	def num_unique_types(self):
		pass

	def all_same(self):
		#what if empty list?
		return len(set(self.unit_ids)) == 1

	def types(self):
		"""Returns the names and types of the units"""
		pass

	def primary_type(self):
		pass

	def same_side(self):
		"""Checks if all units have matching or 'Any' side values"""
		return len(set(unit['Side'] for unit in self.units) - set(['Any'])) <= 1

	@classmethod
	def from_cost(cls, cost):
	#code works, but needs side logic
	#can add tfid or name = random+cost
	#could pass side as parameter
		unit_list = []
		while cost > 200:
			unit_id = random.choice(list(cls.live_units))
			unit_cost = cls.live_units[unit_id]['Cost']
			if unit_cost <= cost:
				unit_list.append(unit_id)
				cost -= unit_cost
		return cls(unit_list)

	@classmethod
	def from_count(cls, count):
	#could pass in side as param
		unit_list = []
		while count > 0:
			unit_id = random.choice(list(cls.live_units))
			unit_list.append(unit_id)
			count -= 1
		return cls(unit_list)

	def space_left(self):
		#if loadable, returns how much space is left, else 0
		pass

	@classmethod
	def from_size(cls, size):
		#size is how much transport space is left
		pass

	@classmethod
	def from_aimd(cls, aimd_tf, tfid):
		tf = {'tfid': tfid}
		temp_list = list()
		for key, data in aimd_tf.items():
			if key.lower() == 'name':
				tf['name'] = data
			elif key.lower() == 'group':
				tf['group'] = data
			else:
				count, unit = data.split(',')
				new_units = [unit] * int(count)
				temp_list.extend(new_units)
		if set(temp_list) <= set(cls.live_units):
			tf['unit_ids'] = temp_list
			if len(temp_list) > 0:
				return cls(**tf)

	@classmethod
	def load_aimd(cls, aimd_file):
		#contains setup and loop for loading all sections from aimd.ini
		#calls Taskforce.from_aimd for actual taskforce construction
		with open(aimd_file) as ai:
			ai_text = ai.read()
		aimd_config = cls.config_setup(ai_text)

		for tfid in set(aimd_config['TaskForces'].values()):
			if aimd_config.has_section(tfid):
				tf = aimd_config[tfid]

				if any(line[0].isdigit() for line in tf.keys()):
					new_tf = cls.from_aimd(tf, tfid)
					if new_tf:
						yield tfid, new_tf

	@classmethod
	def load_rules(cls, rules_file):
		with open(rules_file) as rf:
			rules_lines = [line.split(';')[0].strip() for line in rf.readlines()]
			#drops all comments from rulesmd for better parsing

		joined = '\n'.join(rules_lines)
		rules_config = cls.config_setup(joined)

		types = ['InfantryTypes', 'VehicleTypes', 'AircraftTypes', 'BuildingTypes']

		#gets all units in rulesmd
		all_units = {}
		buildings = {} #buildings aren't needed for side test
		for t in types:
			for unit_id in rules_config[t].values():
				if rules_config.has_section(unit_id):
					if t == 'BuildingTypes':
						buildings[unit_id] = cls.clean(rules_config[unit_id], unit_id, t)
					else:
						all_units[unit_id] = cls.clean(rules_config[unit_id], unit_id, t)

		#filters down to units that can be built
		for unit_id, unit in all_units.items():
			if unit['TechLevel'] != -1 and unit['TechLevel'] != 11:
				if 'AILOCK' not in unit['Prerequisite']:
					cls.live_units[unit_id] = unit

		for unit_id, unit in cls.live_units.items():
			unit['Side'] = cls.find_side(unit, buildings)

	@staticmethod
	def clean(unit, unit_id, unit_type):
		lists = ['Owner', 'RequiredHouses','ForbiddenHouses', 'VeteranAbilities', 'EliteAbilities',
				 'SecretHouses', 'Prerequisite']

		unit = dict(unit)
		for key, value in unit.items():
			
			#converts to bool
			test_val = value.lower()
			if test_val == 'yes' or test_val == 'true':
				unit[key] = True
			elif test_val == 'no' or test_val == 'false':
				unit[key] = False
			
			#converts to list
			elif value.count(',') > 0 or key in lists:
				unit[key] = [v.strip() for v in value.split(',')]
		
			#try to convert to number
			else:
				try:
					new_num = float(value)
					unit[key] = new_num
				except:
					pass

		if unit_type == 'BuildingTypes':
			return unit

		#sets default values
		unit['Passengers'] = unit.get('Passengers', 0)
		unit['SizeLimit'] = unit.get('SizeLimit', 0)
		unit['Size'] = unit.get('Size', 1000)
		unit['TechLevel'] = unit.get('TechLevel', -1)
		unit['UnitID'] = unit_id
		unit['Underwater'] = unit.get('Underwater', False)
		unit['ConsideredAircraft'] = unit.get('ConsideredAircraft', False)
		unit['Naval'] = unit.get('Naval', False)
		unit['ForbiddenHouses'] = unit.get('ForbiddenHouses', [])
		unit['RequiredHouses'] = unit.get('RequiredHouses', [])
		unit['SecretHouses'] = unit.get('SecretHouses', [])

		return unit

	@staticmethod
	def find_side(unit, buildings):
		"""Does rough side assignment to units."""
		allies = set(['British', 'French', 'Germans', 'Americans', 'Alliance'])
		soviets = set(['Russians', 'Confederation', 'Africans', 'Arabs'])
		yuri = set(['YuriCountry'])
		any_side = allies | soviets | yuri

		owners = set(unit['Owner'])
		forbidden = set(unit['ForbiddenHouses'])
		required = set(unit['RequiredHouses']) | set(unit['SecretHouses'])
		allowed = owners - forbidden

		for condition in [required, allowed]:
			if len(condition & any_side) == len(any_side):
				return 'Any'
			elif len(condition & allies) > 0:
				return 'Allied'
			elif len(condition & soviets) > 0:
				return 'Soviet'
			elif len(condition & yuri) > 0:
				return 'Yuri'

	@staticmethod
	def config_setup(text):
		config = configparser.ConfigParser(strict=False)
		config.optionxform = lambda option: option
		config.read_string(text)
		return config

	def to_aimd(self):
		self.reorder() #defaults to transports first
		c = Counter(unit['UnitID'] for unit in self.units)
		lines = []
		for unit, count in c.items():
			line = '{},{}'.format(count, unit)
			lines.append(line)

		aimd_tf = dict(enumerate(lines))
		aimd_tf['Group'] = -1
		return {self.tfid: aimd_tf}

	def __str__(self):
		return ', '.join([unit['Name'] for unit in self.units])

























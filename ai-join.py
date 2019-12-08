import configparser
import os
import random
import time

def config_setup(filename):
	config = configparser.ConfigParser(strict=False)
	config.optionxform = lambda option: option
	config.read(filename)
	return config

def gen_new_id(all_ids, file_ids):
	new_id = str(random.randint(0, 10000000)) + '-G'
	while new_id in (all_ids | file_ids):
		new_id = str(random.randint(0, 10000000)) + '-G'
	return new_id

#Takes a ConfigParser object, returns a dict(key: list) format
def read_triggers(config):
	trigger_dict = {}
	for key, value in config['AITriggerTypes'].items():
		trigger_dict[key] = value.split(',')
	return trigger_dict

def write_triggers(triggers):
	for key, value in triggers.items():
		triggers[key] = ','.join(value)
	return {'AITriggerTypes': triggers}

def fix_trigger_ids(triggers, file_ids, all_ids, file_changed_ids):
#triggers = {'t_id': ['name','team1','owner','tech_level','type','trigger',
# 			'condition', 'start','min','max','skirmish','unknown','side',
#			'base_def','team2','easy','med','hard']}
	for key, value in triggers.items():

		team1_id = value[1]
		if team1_id in file_changed_ids:
			triggers[key][1] = file_changed_ids[team1_id]

		team2_id = value[14]
		if team2_id in file_changed_ids:
			triggers[key][14] = file_changed_ids[team2_id]

		if key in all_ids:
			new_id = gen_new_id(all_ids, file_ids)
			all_ids.add(new_id)
			file_changed_ids[key] = new_id
			triggers[new_id] = triggers[key]
			del triggers[key]

	return triggers

files = [f for f in os.listdir() if f.endswith('.ini')]
if len(files) < 2:
	print('Not enough files!')
	quit()

#Loads the files largest to smallest for less work
files = sorted(files, key=lambda f: os.stat(f).st_size)
print('Found {} files to join: {}'.format(len(files), list(reversed(files))))
print('Adding:', files[-1])
output_config = config_setup(files.pop())
files = reversed(files)

#setup tracking variables
types_lists = ['TaskForces', 'ScriptTypes', 'TeamTypes', 'AITriggerTypes']
all_ids = set(output_config.sections() + output_config.options('AITriggerTypes'))
num_scripts = len(output_config.options('ScriptTypes'))
num_teams = len(output_config.options('TeamTypes'))
output_triggers = read_triggers(output_config)

for file in files:
	print('Adding:', file)
	f_config = config_setup(file)
	file_ids = set(f_config.sections() + f_config.options('AITriggerTypes'))
	file_changed_ids = {}

	for t in types_lists[:3]:
		file_list = [i for i in f_config[t].values()]
		matching_ids = all_ids & set(file_list)
		
		type_changed_ids = {}
		for i in matching_ids:
			new_id = gen_new_id(all_ids, file_ids)
			all_ids.add(new_id)
			type_changed_ids[i] = new_id

		new_list = [type_changed_ids.get(i, i) for i in file_list]
		old_output_list = [i for i in output_config[t].values()]
		combined_list = old_output_list + new_list

		if t == 'TeamTypes':
			offset = 1
		else:
			offset = 0

		numbered_list = dict(enumerate(combined_list, start=offset))
		output_list = {t: numbered_list}
		output_config.remove_section(t)
		output_config.read_dict(output_list)

		new_type_sections = {}
		for key, value in type_changed_ids.items():
			new_type_sections[value] = dict(f_config[key].items())
			f_config.remove_section(key)
		f_config.read_dict(new_type_sections)

		file_changed_ids.update(type_changed_ids)

		if t == 'ScriptTypes':
			for script in set(new_list):
				for line, val in f_config[script].items():
					if not line.isdigit():
						continue
					part1, part2 = val.split(',')
					if part1 == '17': #fixes reference number for change_script
						new_val = part1 + ', ' + str(int(part2) + num_scripts)
						f_config[script][line] = new_val
					elif part1 == '18': #fixes reference number for change_team
						new_val = part1 + ', ' + str(int(part2) + num_teams)
						f_config[script][line] = new_val
			num_scripts += len(new_list)

		elif t == 'TeamTypes':
			for team in set(new_list):

				team_script = f_config[team]['Script']
				if team_script in file_changed_ids:
					f_config[team]['Script'] = file_changed_ids[team_script]

				team_tforce = f_config[team]['TaskForce']
				if team_tforce in file_changed_ids:
					f_config[team]['TaskForce'] = file_changed_ids[team_tforce]

			num_teams += len(new_list)

	all_ids = all_ids | set(f_config.sections())

	file_triggers = read_triggers(f_config)
	file_triggers = fix_trigger_ids(file_triggers, file_ids, all_ids, file_changed_ids)
	output_triggers.update(file_triggers)

	#removes the types_lists from f_config, since already added to output_config
	for t in types_lists:
		f_config.remove_section(t)
	f_config.remove_section('Digest')
	
	output_config.read_dict(f_config)

output_config.remove_section('AITriggerTypes')
output_config.read_dict(write_triggers(output_triggers))

print('All files joined')
print('Creating joined.ini')

with open('joined.ini', 'w') as output:
	output_config.write(output, space_around_delimiters=False)

print('Closing in 10 seconds')
time.sleep(10)
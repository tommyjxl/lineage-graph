import re
import json
import argparse
import pandas as pd
from pathlib import Path


def to_table(scan_path, output_dir, type_filter):
	paths = []
	for path in Path(scan_path).rglob('*.manifest'):
	    paths.append(path.absolute())

	output_to_type = {}

	dependency_map = {}
	raw_table = {}
	name_to_index = {}
	i = 0
	for path in paths:
		with open(path) as f:
			d = json.loads(f.read())
			output_to_type[d['output']] = d['type']

			if re.findall(type_filter, d['type']):
				output = d['output']
				inputs = [x for x in d['inputs']]
				dependency_map[output] = inputs
				name_to_index[output] = i
				i += 1
				raw_table[output] = []

	num_tables = len(raw_table.keys())

	for k in raw_table:
		raw_table[k] = [''] * num_tables

	df = pd.DataFrame(data=raw_table)

	missing_keys = set()

	for k in dependency_map:
		df[k][name_to_index[k]] = 'O'
		for i in dependency_map[k]:
			try:
				df[k][name_to_index[i]] = 'I'
			except KeyError as ex:
				missing_keys.add(str(ex).strip("'"))

	df.to_csv(output_dir + '/dependencies.csv')

	num_missing_keys = len(list(missing_keys))
	with open(output_dir + '/manifest2table_errors.json', 'w') as f:
		f.write(json.dumps({"KeyError": list(missing_keys)}, indent=2))

	with open(output_dir + '/output_to_type.json', 'w') as f:
		f.write(json.dumps(output_to_type, indent=2))

	print('%s missing keys detected. Refer to manifest2table_errors.json and check manifest files.' % num_missing_keys)
	print('Output directory: %s' % output_dir)
	print('Table dimensions: %s' % str(df.shape))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', default='../big_query')
    parser.add_argument('--type_filter', default='table|view')
    parser.add_argument('--output_dir', default='output')
    args = parser.parse_args()
    to_table(args.input_dir, args.output_dir, args.type_filter)

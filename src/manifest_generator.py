import re
import os
import json
import argparse
from pathlib import Path

missing_paths = set()
valid_paths = []

paths = []


def get_cfg_val(key, content):
	pattern = r"%s=(\"[\w-]+\")" % key
	return re.search(pattern, content).group().lstrip("%s=" % key).strip('"')


def generate_manifest(path, output_name, output_dir_path, output_type):
	manifest = {"type": output_type, "output": output_name, "inputs": None}
	try:
		with open(path) as f:
			content = f.read()
	except Exception as ex:
		missing_paths.add(str(path))
		return None

	valid_paths.append(str(path))

	dependencies = set()

	# Rules for SQL statements
	# Copied from https://source.golabs.io/bi/source-finder/-/blob/master/sourcefinder/core/query_parser.py#L57
	pattern = re.compile(r'(?:FROM|JOIN)\s+`?([\w-]+\.[\w-]+\.[\w]+|[\w-]+\.[\w]+)`?',re.IGNORECASE)
	output = pattern.findall(content)
	for parts in output:
		if parts != '' and parts != output_name:
			dependencies.add(parts)
	manifest["inputs"] = list(dependencies)

	with open('%s/%s.manifest' % (output_dir_path, output_name), 'w') as f:
		f.write(json.dumps(manifest, indent=2))
		return True

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--input_dir', default='../big_query')
	parser.add_argument('--output_dir', default='output')
	args = parser.parse_args()

	# delete old manifests
	for path in Path(args.input_dir).rglob('*.manifest'):
	    os.remove(path.absolute())

	for path in Path(args.input_dir).rglob('properties.cfg'):
		paths.append(path.absolute())

	file_count = 0
	for path in paths:
		with open(path) as f:
			content = f.read()

		try:
			project = get_cfg_val("BQ_PROJECT_ID", content)
		except Exception as ex:
			missing_paths.add(str(path))

		try:
			dataset_id = get_cfg_val("BQ_DATASET_ID", content)
		except Exception as ex:
			missing_paths.add(str(path))

		try:
			table_id = get_cfg_val("BQ_TABLE_ID", content)
			bq_table = "%s.%s.%s" % (project, dataset_id, table_id)
			path_to_sql = path.parents[1] / ("pg_sql/%s.sql" % table_id)
			if generate_manifest(path_to_sql, bq_table, str(path.parents[1] / "configs"), "table"):
				file_count += 1
		except Exception as ex:
			missing_paths.add(str(path))

		try:
			view_id = get_cfg_val("BQ_VIEW_ID", content)
			bq_view = "%s.%s.%s" % (project, dataset_id, view_id)
			path_to_sql = path.parents[1] / ("pg_sql/%s.sql" % view_id)
			if generate_manifest(path_to_sql, bq_view, str(path.parents[1] / "configs"), "view"):
				file_count += 1
		except Exception as ex:
			missing_paths.add(str(path))

	if not os.path.exists(args.output_dir):
	    os.makedirs(args.output_dir)
    
	with open('%s/manifest_overview.json' % args.output_dir, 'w') as f:
		f.write(json.dumps({"valid_paths_count": len(valid_paths), "missing_paths_count": len(missing_paths), "valid_paths": valid_paths, "missing_paths": list(missing_paths)}, indent=2))
	
	print("Total config files found: %s" % len(paths))
	print("Manifest files generated: %s" % file_count)
	print('For full diagnostic refer to ' + '%s/manifest_overview.json' % args.output_dir)

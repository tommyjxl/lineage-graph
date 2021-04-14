#!/usr/bin/env bash

pip install -r requirements.txt &&

python manifest_generator.py --input_dir "../big_query" --output_dir "../data" &&

python manifest2table.py --input_dir "../big_query" --type_filter "table|view" --output_dir "../data" &&

## sample for filtering the lineage of my_dataset.my_table only
#python table2graph.py --input "../data/dependencies.csv" --output_dir "../data" --filter "(project_id\.my_dataset\.my_table)" &&

## sample for filtering all tables that belong to my_dataset dataset and has xyz in their name
#python table2graph.py --input "../data/dependencies.csv" --output_dir "../data" --filter "(.*\\.my_dataset\\..*xyz*)" &&

## sample for filtering all tables belonging to my_dataset and old_dataset datasets
#python table2graph.py --input "../data/dependencies.csv" --output_dir "../data" --filter "(project_id\\.(my_dataset|old_dataset)\\..(.*?))" &&

## Sample for wildcard entry - allows all tables.
python table2graph.py --input "../data/dependencies.csv" --output_dir "../data" --filter "(.*?)" &&

open -a /Applications/Google\ Chrome.app/ force-graph.html --args --allow-file-access-from-files --allow-file-access --allow-cross-origin-auth-prompt

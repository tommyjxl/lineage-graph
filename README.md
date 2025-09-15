# lineage-graph
Graph generator for expressing lineage between data source and a visualisation demo
![image info](graph-animation.gif)

## Process Overview
1) Generate manifest files for each BQ-to-BQ task (for compatible config and sql file)
2) Create a dependency table (of input and output tables) based on all manifest files
3) Create a json representation of the graph
4) Visualise the graph

## Quickstart (Mac OS)
`./run_demo.sh`
For the first run, you may be prompted to grant the terminal certain permissions.

## Manually view the visualized graph:
`python -m http.server`
Open a browser and go to `http://localhost:8000/`
Click `force-graph.html` to load the graph

## Running individual steps:
This assumes that a project with SQL files to be parsed a specific way.
For other types of parsing, the manifest_generator will be need to be updated.

`cd <path/to/lineage-graph/src> && ./run.sh` OR

`python manifest_generator.py --input_dir <input_directory> --output_dir <output_directory>`

`python manifest2table.py --input_dir <input_directory> --filter "(.*\\.my_dataset\\..*xyz*)"`

`python table2graph.py --input <path/to/dependencies.csv> --output_dir <output_directory>`

To visualise the graph, output directory should be `<path/to/lineage-graph/data>`
Run the demo from lineage-graph root:
`cd <path/to/lineage-graph && ./run_demo.sh`

Summary of output files:

	- Manifest files in the same directories where compatible properties.cfg were found

	- manifest_overview.json -> reports manifest file paths and issues in manifest generation

	- dependencies.csv -> CSV representation of dependencies (import to gsheet for a tabular view of the dependencies)

	- manfest2table_errors.json -> reports issues in generator

	- output_to_type.json -> node name to type mapping (tables vs views)

	- node_analysis.json -> metrics for each node

	- dataset.json -> JSON representation of the graph, for force-graph.html to import

## Filters:
manifest2table.py arguments allow for regex-based filtering:
Fill them with the regex pattern to generate a subset of the dependency table. Example:

`python table2graph.py --input "../data/dependencies.csv" --output_dir "../data" --filter "(project_id\\.(my_dataset|old_dataset)\\..(.*?))`


## To customize colors:
Edit table2graph.py global variables - replace with your RGB(A) values
```
CONSUMER_COLOR = (213.0/255.0, 94.0/255.0, 0.0/255.0)
PRODUCER_COLOR = (0.0/255.0, 158.0/255.0, 115.0/255.0) 
MIN_COLOR = (0.0, 0.0, 0.0)
FILTERED_LINK_TO_TARGET_NODE_COLOR = 'rgba(204, 121, 167, 0.5)'
FILTERED_LINK_TO_SOURCE_NODE_COLOR = 'rgba(0, 114, 178, 0.5)'
LINK_DEFAULT_COLOR = 'rgba(50, 50, 50, 0.1)'
```

## To obfuscate the names of datasources in graph visualisation:
`python obsucator.py`

## To add on-hover labelling of neighbour nodes, use this in force-graph.html:
```
  // labelling of all neighbours
  if (node != hoverNode) {
    ctx.font = `9px Sans-Serif`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = 'magenta'
    ctx.fillText(node.label, node.x + 10, node.y);
  }
```

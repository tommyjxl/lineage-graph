import re
import csv
import json
import random
import argparse
from itertools import chain

import numpy as np
import operator
import networkx as nx
import networkx.algorithms as algo
import matplotlib.pyplot as plt
from networkx.algorithms import approximation
from networkx.algorithms.dag import ancestors,descendants
from math import sqrt
from pyvis.network import Network

DATA_ROW_START_INDEX = 1
BQ_TABLE_COLUMN_START_INDEX = 1

# change me for different color theme
CONSUMER_COLOR = (213.0/255.0, 94.0/255.0, 0.0/255.0)
PRODUCER_COLOR = (0.0/255.0, 158.0/255.0, 115.0/255.0) 
MIN_COLOR = (0.0, 0.0, 0.0)
FILTERED_LINK_TO_TARGET_NODE_COLOR = 'rgba(204, 121, 167, 0.5)'
FILTERED_LINK_TO_SOURCE_NODE_COLOR = 'rgba(0, 114, 178, 0.5)'
LINK_DEFAULT_COLOR = 'rgba(50, 50, 50, 0.1)'

DISPLAY_PAGE_WIDTH = "1024px"
DISPLAY_PAGE_HEIGHT = "768px"


def tuple_to_hex_rgb(t, denominator):
	for i in range(0, 3):
		if t[i] > 1.0:
			t[i] = t[i] / denominator

	def float_to_hex(f):
		s = hex(int(f*255.0))
		if not s or s == '0x0':
			return '00'
		return s.split('x')[-1].zfill(2)

	return '#%s%s%s' % (float_to_hex(t[0]), float_to_hex(t[1]), float_to_hex(t[2]))

def color_shader(node):
	consumer_color = MIN_COLOR + np.multiply(float(node["depends_on_count"]), CONSUMER_COLOR)
	producer_color = np.add(MIN_COLOR, np.multiply(float(node["consumed_by_count"]), PRODUCER_COLOR))
	node["color"] = tuple_to_hex_rgb(np.add(consumer_color, producer_color), float(node["depends_on_count"])+float(node["consumed_by_count"]))

def get_top_N(d, N, title):
	s = title + "\r\n"
	ordered = {k: v for k, v in reversed(sorted(d.items(), key=lambda item: item[1]))}
	for idx, o in enumerate(ordered):
		if idx > N-1:
			break
		s += "%s: %s\r\n" % (o.replace('\n', '.'), ordered[o])
	s += "\r\n"
	return s

class Csv2Graph():
	def __init__(self, csvData, output_dir, filter):
		self.csvData = csvData
		self.output_dir = output_dir
		self.filter_pattern = re.compile(filter, re.IGNORECASE)
		self.filter_raw = filter
		self.target_nodes = set()

	def read_csv(self):
		self.list_data = []
		idx = 0
		for row in csvData:
			self.list_data.append(row)
			idx += 1
			#if idx > 100:
			 #  break 

	def tidy_bq_names(self):
		self.relabel_map = {}

		with open('output/output_to_type.json') as f:
			output_to_type = json.loads(f.read())

		for row in self.list_data[DATA_ROW_START_INDEX:]:
			for idx, v in enumerate(row[BQ_TABLE_COLUMN_START_INDEX:]):  # find the output
				if v == 'O':
					c = self.list_data[0][BQ_TABLE_COLUMN_START_INDEX+idx]
					self.relabel_map[c] = output_to_type.get(c, 'unknown_type') + ':' + c
					break


	def build_graph(self):
		datalineage_graph = nx.DiGraph()
	
		for row in self.list_data[DATA_ROW_START_INDEX:]:
			target_node = None
			for idx, v in enumerate(row[BQ_TABLE_COLUMN_START_INDEX:]):  # find the output
				if v == 'O':
					target_node = self.list_data[0][BQ_TABLE_COLUMN_START_INDEX+idx]
					filter_full_match = True if (self.filter_raw != '(.*?)' and self.filter_pattern.fullmatch(target_node.split(':')[-1])) else False
					datalineage_graph.add_node(target_node, id=target_node, entity="node", value=1, size=10, filter_full_match=filter_full_match)
					break

			for idx, v in enumerate(row[BQ_TABLE_COLUMN_START_INDEX:]):  # find the input
				if v == 'I' and target_node:
					datalineage_graph.add_edge(target_node, self.list_data[0][BQ_TABLE_COLUMN_START_INDEX+idx],
						relationship="consumed_by", entity="link", value=1)

		edges = datalineage_graph.edges()
		node_names = datalineage_graph.nodes()

		filtered_nodes = set()
		node_color = {}

		#get nodes that match the pattern
		for node in datalineage_graph.nodes():
			if self.filter_pattern.fullmatch(node):
				self.target_nodes.add(node)



		#get all the Ancestors and descendants of the identified nodes from the digraph:
		for node in self.target_nodes:
			# print("Node: ", node)
			# print("Ancestors: ", ancestors(datalineage_graph, node))
			# print("Descendents: ", descendants(datalineage_graph, node))
			filtered_nodes.add(node)
			filtered_nodes.update(ancestors(datalineage_graph, node))
			filtered_nodes.update(descendants(datalineage_graph, node))


		self.G = datalineage_graph.subgraph(list(filtered_nodes))

		print('Node count: %s' % self.G.number_of_nodes())
		print('Edge count: %s' % self.G.number_of_edges())
   
		nx.write_graphml(self.G, "data_lineage.graphml")

	def relabel(self):
		self.H = nx.relabel_nodes(self.G, self.relabel_map, copy=True)


	def add_metadata(self):
		self.nt = Network(height=DISPLAY_PAGE_HEIGHT, width=DISPLAY_PAGE_WIDTH, directed=True, bgcolor="#090909", heading="BI Apps data lineage for :"+self.filter_raw)
		self.nt.from_nx(self.H)

		for node in self.nt.nodes:
			node["consumed_by_count"] = len(self.H.out_edges(node["id"]))
			node["depends_on_count"] = len(self.H.in_edges(node["id"]))

		for node in self.nt.nodes:
			color_shader(node)


	def export_json(self):
		_attrs = dict(id='id', source='source', target='target', key='key')
		
		# This is stolen from networkx JSON serialization. It basically just changes what certain keys are.
		def node_link_data(G, attrs=_attrs):
			multigraph = G.is_multigraph()
			id_ = attrs['id']
			source = attrs['source']
			target = attrs['target']
			# Allow 'key' to be omitted from attrs if the graph is not a multigraph.
			key = None if not multigraph else attrs['key']
			if len(set([source, target, key])) < 3:
				raise nx.NetworkXError('Attribute names are not unique.')
			data = {}
			data['directed'] = G.is_directed()
			data['multigraph'] = multigraph
			data['graph'] = G.graph
			data['nodes'] = [dict(chain(G.nodes[n].items(), [(id_, n), ('label', n)])) for n in G]

			for node in self.nt.nodes:
				for x in data['nodes']:
					if x['id'] == node['id']:
						x['color'] = node['color']
						x['type'] = node['label'].split(':')[0]
						break

			if multigraph:
				data['links'] = [
					dict(chain(d.items(),
							  [('source', u), ('target', v), (key, k), ('curvature', random.uniform(-0.1, 0.1))]))
					for u, v, k, d in G.edges(keys=True, data=True)]
			else:
				data['links'] = [
					dict(chain(d.items(),
							  [('source', u), ('target', v), ('curvature', random.uniform(-0.1, 0.1))]))
					for u, v, d in G.edges(data=True)]

			# link/edge coloring
			for link in data['links']:
				for node in data['nodes']:
					if self.filter_raw != '(.*?)' and (link['target'].split(":")[1]).strip() in self.target_nodes:
						link['color'] = FILTERED_LINK_TO_TARGET_NODE_COLOR
					elif self.filter_raw != '(.*?)' and (link['source'].split(":")[1]).strip() in self.target_nodes:
						link['color'] = FILTERED_LINK_TO_SOURCE_NODE_COLOR
					else:
						link['color'] = LINK_DEFAULT_COLOR

			return data
	 
		with open(self.output_dir + '/dataset.json', 'w') as f:
		  f.write(json.dumps({'nodes': node_link_data(self.H)['nodes'], 'links': node_link_data(self.H)['links']}, indent=4))

		

	def print_analytics(self):
		MAX_OUT_EDGES = 0
		node_stats = {}
		node_names = self.G.nodes()
		for n in node_names:
			l = len(self.G.out_edges(n))
			i = len(self.G.in_edges(n))

			node_stats[n] = {"in_edges": i, 
							 "out_edges": l, 
							 "degree_centrality": None, 
							 "trophic_levels": None,
							 "average_neighbor_degree": None}

			MAX_OUT_EDGES = max(MAX_OUT_EDGES, l)


		'''
		Historically first and conceptually simplest is degree centrality, 
		which is defined as the number of links incident upon a node (i.e., the number of ties that a node has). 
		The degree can be interpreted in terms of the immediate risk of a node for catching whatever is 
		flowing through the network (such as a virus, or some information).
		Ie. Higher values mean the table has the most links to other tables
		'''
		degree_centrality = algo.degree_centrality(self.G)
		for c, v in degree_centrality.items():
			node_stats[c]["degree_centrality"] = v

		'''
		A food web starts at trophic level 1 with primary producers such as plants, can move to herbivores at level 2,
		carnivores at level 3 or higher, and typically finish with apex predators at level 4 or 5
		Ie. Higher values mean the table is more likely to be a heavy consumer rather than producer
		'''
		trophic_levels = algo.trophic_levels(self.G)
		for c, v in trophic_levels.items():
			node_stats[c]["trophic_levels"] = v

		'''
		The average nearest neighbor degree (ANND) of a node of degree k is widely used to 
		measure dependencies between degrees of neighbor nodes in a network.
		Ie. Higher values mean higher dependency on neighbour nodes
		'''
		average_neighbor_degree = algo.average_neighbor_degree(self.G)
		for c, v in average_neighbor_degree.items():
			node_stats[c]["average_neighbor_degree"] = v

		readable_note_stats = {}
		for k in node_stats:
			readable_note_stats[k.replace('\n', '.')] = node_stats[k]

		with open(self.output_dir + "/nodes_analysis.json", 'w') as f:
			f.write(json.dumps(readable_note_stats, indent=2))

	def run(self):
		self.read_csv()
		self.tidy_bq_names()
		self.build_graph()
		self.relabel()
		self.add_metadata()
		self.print_analytics()
		self.export_json()


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--input', default='output/dependencies.csv')
	parser.add_argument('--output_dir', default='output')
	parser.add_argument('--filter', default="(.*?)")
	args = parser.parse_args()

	with open(args.input) as f:
		reader = csv.reader(f)
		csvData = list(reader)

	c2g = Csv2Graph(csvData, args.output_dir, args.filter)
	c2g.run()
	print('execution complete')
		
import json
import hashlib

def obfuscate(x):
	return x.split(':')[0] + ':' + hashlib.md5(x.split(':')[1].encode('utf-8')).hexdigest()

with open('output/dataset.json') as f:
	d = json.loads(f.read())

for n in d['nodes']:
	n['id'] = obfuscate(n['id'])
	n['label'] = obfuscate(n['label'])

for l in d['links']:
	l['source'] = obfuscate(l['source'])
	l['target'] = obfuscate(l['target'])

with open('output/dataset.json', 'w') as f:
	f.write(json.dumps(d, indent=2))

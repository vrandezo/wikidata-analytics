# trafo -> png
import gzip
	
count = 0

graphs = {}
for line in gzip.open('geograph.txt.gz'):
	if line.startswith('#') : continue
	s, p, o = line.strip().split(' ')
	if p not in graphs :
		graphs[p] = {}
	if s not in graphs[p] :
		graphs[p][s] = []
	graphs[p][s].append(o)

output = open('graph.js', 'w')
output.write("var graph = {\n") 
for p in graphs :
	output.write('  "' + p + '" : {' + "\n")
	for s in graphs[p] :
		output.write('    "' + s + '" : ' + str(graphs[p][s]) + ",\n")
	output.write("  },\n")
output.write('};')
output.close()

print "Finished."

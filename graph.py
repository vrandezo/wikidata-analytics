# projects the full knowledge base into a simple graph, only having
# the connections between items
# needs kb
import gzip

output = gzip.open('graph.txt.gz', 'w')
count = 0
linecount = 0
for line in gzip.open('kb.txt.gz') :
	linecount += 1
	if (linecount % 1000000) == 0 : print linecount / 1000000
	if line.startswith('#') :
		output.write(line)
		continue
	if line.startswith(' ') : continue
	parts = line.split(' ')
	if len(parts) != 4 : continue
	s = parts[0]
	p = parts[1]
	o = parts[2]
	if not s.startswith('Q') : continue
	if not p.startswith('P') : continue
	if not o.startswith('Q') : continue
	output.write(s + ' ' + p + ' ' + o + "\n")
	count += 1
print linecount, 'lines'
print count, 'results'
output.close()

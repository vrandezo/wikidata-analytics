# gets all properties and their datatypes
# needs kb
import gzip

output = open('types.txt', 'w')
count = 0
linecount = 0
pcount = {}
ptype = {}
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
	if p.startswith('P') :
		if p not in pcount :
			pcount[p] = 0
		pcount[p] += 1 
	if p == 'type' :
		ptype[s] = o
		if s not in pcount :
			pcount[s] = 0
		count += 1

for p in ptype :
	output.write(p + ' ' + ptype[p] + ' ' + str(pcount[p]) + "\n")
output.write('# ' + str(count) + " results\n")

print linecount, 'lines'
print count, 'results'
output.close()

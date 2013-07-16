# gets all properties and their datatypes
# needs kb
import gzip

output = open('types.txt', 'w')
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
	if not p == 'type' : continue
	output.write(s + ' ' + o + "\n")
	count += 1
print linecount, 'lines'
print count, 'results'
output.close()

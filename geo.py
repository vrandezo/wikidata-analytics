# gets all coordinates in the main snak
# needs kb
import gzip

output = gzip.open('geo.txt.gz', 'w')
count = 0
linecount = 0
for line in gzip.open('kb.txt.gz') :
	linecount += 1
	if (linecount % 1000000) == 0 : print linecount / 1000000
	if line.startswith('#') :
		output.write(line)
		continue
	if line.startswith(' ') : continue
	parts = line.split(' ', 2)
	if len(parts) != 3 : continue
	s = parts[0]
	p = parts[1]
	o = parts[2]
	if not p.startswith('P') : continue
	if not o.startswith("{'latitude':") : continue
	o = o[:-2]
	o = eval(o)
	output.write(str(o['latitude']) + ' ' + str(o['longitude']) + "\n")
	count += 1
print linecount, 'lines'
print count, 'results'
output.close()

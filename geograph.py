# gets the graph between all geotagged items
# needs geo and graph
import gzip

linecount = 0
geoitems = set()
for line in gzip.open('geo.txt.gz') :
	linecount += 1
	if (linecount % 1000000) == 0 : print linecount / 1000000
	if line.startswith('#') :
		continue
	lat, long, p, s = line.strip().split(' ')
	geoitems.add(s)
print linecount, 'lines'
print len(geoitems), 'geoitems'

output = gzip.open('geograph.txt.gz', 'w')

count = 0
linecount = 0
for line in gzip.open('graph.txt.gz') :
	linecount += 1
	if (linecount % 1000000) == 0 : print linecount / 1000000
	if line.startswith('#') :
		output.write(line)
		continue
	s, p, o = line.strip().split(' ')
	if s in geoitems and o in geoitems :
		output.write(line)
		count += 1

print linecount, 'lines'
print count, 'results'

output.close()

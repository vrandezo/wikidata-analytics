# projects all tuples connected with a property, dropping qualifiers and references
# needs the graph
import sys, gzip

if len(sys.argv) < 2 :
	print 'no property id given'
	exit()
propertyid = sys.argv[1]
if not propertyid.isdigit() :
	print property, 'is not a property id'
	exit()
propertyid = int(propertyid)

output = open('data/P' + str(propertyid) + '.txt', 'w')
count = 0
linecount = 0

for line in gzip.open('graph.txt.gz') :
	if line.startswith('#') :
		output.write(line)
		continue
	linecount += 1
	if (linecount % 1000000) == 0 : print linecount / 1000000
	if line.startswith('#') :
		output.write(line)
		continue
	s, p, o = line.split()
	if p == 'P' + str(propertyid) :
		output.write(s + ' ' + o + "\n")
		count += 1

print linecount, 'lines'
print count, 'results'
output.close()

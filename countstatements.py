# counts the number of statements
# needs kb
import gzip

subjects = set()
objects = set()

output = file('stats.txt', 'w')

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
	if not s.startswith('Q') : continue
	p = parts[1]
	o = parts[2]
	if not p.startswith('P') : continue
	subjects.add(s)
	count += 1
	if not o.startswith('Q') : continue
	objects.add(o)

output.write(str(linecount) + 'lines' + "\n")
output.write(str(count) + 'statements' + "\n")
output.write(str(len(subjects)), 'subjects' + "\n")
output.write(str(len(objects)), 'objects' + "\n")
output.write(str(len(subjects.intersection(objects))), 'nodes' + "\n")

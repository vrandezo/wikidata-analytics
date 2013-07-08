# gets all coordinates in the main snak
# needs kb
import gzip

output = gzip.open('geolabel.txt.gz', 'w')
count = 0
linecount = 0
item = ''
enlabel = ''
label = ''
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
	if s != item : 
		item = s
		enlabel = ''
		label = ''
	if p == 'label' :
		if o.startswith('{en:') :
			enlabel = o[4:-4]
		label = o[1:-4]
	if not p.startswith('P') : continue
	if not o.startswith("{'latitude':") : continue
	o = o[:-2]
	o = eval(o)
	if enlabel != '' : label = enlabel
	if label == '' :
		label = s
		print s
	output.write(str(o['latitude']) + ' ' + str(o['longitude']) + ' ' + p + ' ' + s + ' ' + label + "\n")
	count += 1
print linecount, 'lines'
print count, 'results'
output.close()

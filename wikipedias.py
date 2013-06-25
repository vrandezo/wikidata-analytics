# gets all Wikipedias, their language codes, and languages
# needs kb
import gzip

count = 0
linecount = 0

wikipedias = set()
codes = {}
languages = {}

output = open('data/wikipedias.txt', 'w')

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
	if p == 'P31' and o == 'Q52' :
		print 'Wikipedia', s
		wikipedias.add(s)
	if p == 'P424' :
		print 'Code', s, o
		codes[s] = o[1:-1]
	if p == 'P407' :
		#print 'Language', s, o
		languages[s] = o
print linecount, 'lines'

for wikipedia in wikipedias :
	language = languages[wikipedia] if wikipedia in languages else ''
	code = codes[wikipedia] if wikipedia in codes else ''
	language = ' ' + language
	code = ' ' + code
	output.write(wikipedia + code + language + "\n")
	count += 1

output.write('# ' + str(count) + ' entries')
print count, 'results'
output.close()

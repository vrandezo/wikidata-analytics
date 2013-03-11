import bz2, time

print 'Calculating Wikidata stats'

start_time = time.time()

linecount = 0
pagecount = 0
revisioncount = 0
revisionsperitemcount = 0
revisionsperitem = {}
itemcount = 0
itemswithclaims = 0
claimcount = 0
claimsperitem = {}
propertycount = 0
sitelinkcount = 0
labelcount = 0
descriptioncount = 0
item = False
property = True

file = bz2.BZ2File('wikidatawiki-20130228-pages-meta-history.xml.bz2')
for line in file :
	linecount += 1
	if linecount % 1000000 == 0 : print linecount / 1000000

	if line == '  <page>\n' :
		pagecount += 1
		if item :
			sitelinkcount += len(val['links'])
			labelcount += len(val['label'])
			descriptioncount += len(val['description'])
			if 'claims' in val and len(val['claims']) > 0 :
				itemswithclaims += 1
				claimcount += len(val['claims'])
				if not len(val['claims']) in claimsperitem :
					claimsperitem[len(val['claims'])] = 0
				claimsperitem[len(val['claims'])] += 1
			if revisionsperitemcount > 0 :
				if not revisionsperitemcount in revisionsperitem :
					revisionsperitem[revisionsperitemcount] = 0
				revisionsperitem[revisionsperitemcount] += 1
		revisionsperitemcount = 0
		item = False
		property = False
	if line == '    <ns>0</ns>\n' :
		item = True
		itemcount += 1
	if line == '    <ns>120</ns>\n' :
		property = True
		propertycount += 1
	if line == '    <revision>\n' :
		revisioncount += 1
		revisionsperitemcount += 1
	if line.startswith('      <timestamp>') :
		timestamp = line[17:-23]
	if line.startswith('    <title>') :
		title = line[11:-9]
	# checks for anomalies
	if line.startswith('      <text xml:space="preserve">') :
		if item or property :
			if not line.endswith('</text>\n') :
				print line
			else :
				content = line[33:-8]
				content = content.replace('&quot;', '"')
				val = eval(content)
	#if linecount >= 100000 : break

print itemcount, 'items'
print itemswithclaims, 'items with claims'
print claimcount, 'claims'
print 'claims per item', claimsperitem
print propertycount, 'properties'
print sitelinkcount, 'links'
print labelcount, 'labels'
print descriptioncount, 'descriptions'
print pagecount, 'pages'
print revisioncount, 'revisions'
print 'revisions per item', revisionsperitem
print linecount, 'lines'

print time.time() - start_time, 'seconds'
print 'Done.'

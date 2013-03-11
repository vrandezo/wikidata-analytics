#!/usr/bin/env python2
import bz2, time

print 'Calculating Wikidata stats'

start_time = time.time()

bots = ['BeneBot*', 'BetaBot', 'BinBot', 'Choboty', 'Dexbot', 'Hazard-Bot', 'Innocent bot', 'KLBot2', 'Legobot', 'MerlBot', 'MerlIwBot', 'Ra-bot-nik', 'Sk!dbot', 'ThieolBot', 'ValterVBot', 'ZaBOTka']

linecount = 0

# Items
itemcount = 0
itemswithclaims = 0
claimcount = 0
claimsperitem = {}
labelcount = 0
descriptioncount = 0
sitelinkcount = 0
itemrevisioncount = 0
botrevisioncount = 0
revisionsperitem = {}
titleofmostclaims = ""

# Properties
propertycount = 0
propertylabelcount = 0
propertydescriptioncount = 0

# General
pagecount = 0
revisioncount = 0

# temporal variables
# used to save data about a page until this page is fully read
revisionsperitemcount = 0 
title = ""
item = False
property = False

file = bz2.BZ2File('wikidatawiki-latest-pages-meta-history.xml.bz2')
for line in file :
	linecount += 1
	if linecount % 1000000 == 0 : print linecount / 1000000

	if line == '  <page>\n' :
		pagecount += 1
		# Now analyze the previous page, if it was an item or property
		if item :
			sitelinkcount += len(val['links'])
			labelcount += len(val['label'])
			descriptioncount += len(val['description'])
			if 'claims' in val and len(val['claims']) > 0 :
				itemswithclaims += 1
				claimcount += len(val['claims'])
				numberofclaims = len(val['claims'])
				if not numberofclaims in claimsperitem :
					claimsperitem[numberofclaims] = 0
					if max(claimsperitem) <= numberofclaims :
						titleofmostclaims = title
				claimsperitem[len(val['claims'])] += 1
			if revisionsperitemcount > 0 :
				if not revisionsperitemcount in revisionsperitem :
					revisionsperitem[revisionsperitemcount] = 0
				revisionsperitem[revisionsperitemcount] += 1
		if property :
			propertylabelcount += len(val['label'])
			propertydescriptioncount += len(val['description'])
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
		if item:
			itemrevisioncount += 1
			revisionsperitemcount += 1
	if line.startswith('        <username>') :
		username = line[18:-12]
		if item:
			if username in bots:
				botrevisioncount += 1
	if line.startswith('    <title>') :
		title = line[11:-8]
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
	#if linecount >= 1000000 : break

print itemcount, 'items'
print itemswithclaims, 'items with claims'
print claimcount, 'claims'
print 'claims per item', claimsperitem
print 'item with most claims:', titleofmostclaims
print propertycount, 'properties'
print sitelinkcount, 'links'
print labelcount, 'labels'
print propertylabelcount, 'labels (of properties)'
print descriptioncount, 'descriptions'
print propertydescriptioncount, 'descriptions (of properties)'
print pagecount, 'pages'
print revisioncount, 'revisions'
print itemrevisioncount, 'revisions of items'
print botrevisioncount, 'revisions edited by bot'
print 'revisions per item', revisionsperitem
print linecount, 'lines'

print time.time() - start_time, 'seconds'
print 'Done.'

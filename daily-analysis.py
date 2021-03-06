#!/usr/bin/env python2
import sys, bz2, time, gzip, os, urllib, re, bitarray

# This scripts creates the knowledge base and collects a few numbers by going through
# all dailies up to and the latest available dump. This usually runs a few hours.

before = '' # put here '2013-05-01T00:00:00Z' in order to check the state at end of april

def log(txt) :
	print txt

log('Calculating Wikidata stats')

start_time = time.time()

# read the list of bots
log('Loading list of bots')
bots = []
botsjson = urllib.urlopen('http://www.wikidata.org/w/api.php?action=query&list=allusers&augroup=bot&aulimit=500&format=json').read()
botsjson = eval(botsjson)
for bot in botsjson['query']['allusers'] :
	bots.append(bot['name'])
log('List of bots: ' + str(bots))

linecount = 0
charactercount = 0

# Items
itemcount = 0
itemswithclaims = 0
claimcount = 0
claimsperitem = {}
claimswithrefs = 0
refs = 0
itemswithrefs = 0
labelcount = 0
descriptioncount = 0
sitelinkcount = 0
itemrevisioncount = 0
botrevisioncount = 0
revisionsperitem = {}
titleofmostclaims = ''
langlabels = {}
langdescriptions = {}
langsitelinks = {}

# Properties
propertycount = 0
propertylabelcount = 0
propertydescriptioncount = 0

# General
pagecount = 0
revisioncount = 0
processeditems = bitarray.bitarray(2**26) # about 30 M items
processeditems.setall(0)
processedrevisions = bitarray.bitarray(2**28) # about 250 M revisions
processedrevisions.setall(0)
processedproperties = bitarray.bitarray(2**10) # about 1 K properties
processedproperties.setall(0)

boteditsperdate = {}
humaneditsperdate = {}
users = set()

# if there is no data directory, create one
if not os.path.exists('data') :
	os.makedirs('data')
os.chdir('data')

# download the dumps directory file and figure out the date of the latest dump
log('Checking for the date of the last dump')
latestdump = '20121026'
for line in urllib.urlopen('http://dumps.wikimedia.org/wikidatawiki/') :
	if not line.startswith('<tr><td class="n">') : continue
	date = line[27:35]
	if not re.match('\d\d\d\d\d\d\d\d', date) : continue
	log("Checking dump of " + date)
	# check if dump is finished
	finished = False
	for md5 in urllib.urlopen('http://dumps.wikimedia.org/wikidatawiki/' + date + '/wikidatawiki-' + date + '-md5sums.txt') :
		if md5.endswith('-pages-meta-history.xml.bz2' + "\n") :
			finished = True
	if finished :
		latestdump = date
log('Latest dump has been on ' + latestdump)
#latestdump = '20130417'

# download the latest stats if needed
if not os.path.exists('dump' + latestdump) :
	os.makedirs('dump' + latestdump)
os.chdir('dump' + latestdump)
if not os.path.exists('site_stats.sql.gz') :
	log('Downloading stats of the latest dump')
	urllib.urlretrieve('http://dumps.wikimedia.org/wikidatawiki/' + latestdump + '/wikidatawiki-' + latestdump + '-site_stats.sql.gz', 'site_stats.sql.gz')
	
# download the latest dump if needed
if not os.path.exists('pages-meta-history.xml.bz2') :
	log('Downloading latest dump')
	urllib.urlretrieve('http://dumps.wikimedia.org/wikidatawiki/' + latestdump + '/wikidatawiki-' + latestdump + '-pages-meta-history.xml.bz2', 'pages-meta-history.xml.bz2') #xxx

# get the maxrevid of the latest dump
maxrevid = 0
for line in gzip.open('site_stats.sql.gz'):
	if not line.startswith('INSERT INTO') : continue
	stats = eval(line[32:-2])
	maxrevid = int(stats[2])
log('maxrevid of the latest dump: ' + str(maxrevid))

os.chdir('..')

# check the dailies
dailies = []
for line in urllib.urlopen('http://dumps.wikimedia.org/other/incr/wikidatawiki/') :
	if not line.startswith('<tr><td class="n">') : continue
	date = line[27:35]
	if not re.match('\d\d\d\d\d\d\d\d', date) : continue
	dailies.append(date)

# download the dailies in reversed order until the daily maxrevid is smaller than our maxrevid
stopdaily = '20121026'
lastdaily = 0
for daily in reversed(dailies) :
	log('Checking daily of ' + daily)
	if not os.path.exists('daily' + daily) :
		os.makedirs('daily' + daily)
	os.chdir('daily' + daily)
	if not os.path.exists('maxrevid.txt') :
		urllib.urlretrieve('http://dumps.wikimedia.org/other/incr/wikidatawiki/' + daily + '/maxrevid.txt', 'maxrevid.txt')
	dailymaxrevid = int(open('maxrevid.txt').read())
	if dailymaxrevid < maxrevid :
		log('Daily ' + daily + ' is within latest dump')
		stopdaily = daily
		os.chdir('..')
		break
	if not os.path.exists('pages-meta-hist-incr.xml.bz2') :
		log('Downloading daily ' + daily)
		if urllib.urlopen('http://dumps.wikimedia.org/other/incr/wikidatawiki/' + daily + '/status.txt').read() == 'done' :
			urllib.urlretrieve('http://dumps.wikimedia.org/other/incr/wikidatawiki/' + daily + '/wikidatawiki-' + daily + '-pages-meta-hist-incr.xml.bz2', 'pages-meta-hist-incr.xml.bz2') #xxx
			log('Done downloading daily ' + daily)
		else :
			log('Daily not done yet - download aborted')
	os.chdir('..')

def snaktotext(snak) :
	if snak[0] == 'value' :
		if snak[2] == 'wikibase-entityid' :
			return 'P' + str(snak[1]) + ' Q' + str(snak[3]['numeric-id'])
		elif snak[2] == 'string' :
			return 'P' + str(snak[1]) + ' {' + snak[3] + '}'
		elif snak[2] == 'time' :
			return 'P' + str(snak[1]) + ' ' + str(snak[3])
		else :
			log(snak)
			exit()
	elif snak[0] == 'somevalue' :
		return 'P' + str(snak[1]) + ' +'
	elif snak[0] == 'novalue' :
		return 'P' + str(snak[1]) + ' -'
	else :
		log(snak)
		exit()

def processfile(file) :
	global linecount
	global charactercount

	# Items
	global itemcount
	global itemswithclaims
	global claimcount
	global claimsperitem
	global claimswithrefs
	global refs
	global itemswithrefs
	global mostclaims
	global labelcount
	global descriptioncount
	global sitelinkcount
	global itemrevisioncount
	global botrevisioncount
	global titleofmostclaims
	global langlabels
	global langdescriptions
	global langsitelinks

	# Properties
	global propertycount
	global propertylabelcount
	global propertydescriptioncount

	# Filter
	global before
	
	# General
	global revisioncount
	
	global boteditsperdate
	global humaneditsperdate
	global users

	
	# local variables
	title = ''
	item = False
	property = False
	newrev = False
	newtitle = False
	val = {}
	revid = 0
	
	for line in file :
		linecount += 1
		charactercount += len(line)
		if linecount % 1000000 == 0 : log(str(linecount / 1000000))

		# starts a new page
		if line == '  <page>\n' :
			title = ''
			item = False
			property = False
			newrev = False
			newtitle = False
			val = {}
			content = ''
			revid = 0

		if line == '    <revision>\n' :
			revid = 0

		# title
		if line.startswith('    <title>') :
			title = line[11:-9]
			item = title.startswith('Q')
			property = title.startswith('Property:P')
			if item and not processeditems[int(title[1:])] :
				newtitle = True
				processeditems[int(title[1:])] = True
			if property and not processedproperties[int(title[10:])] :
				newtitle = True
				processedproperties[int(title[10:])] = True
				title = title[9:] 

		if line.startswith('      <id>') : # ids of pages have less spaces
			revid = line[10:-6]
			if not processedrevisions[int(revid)] :
				newrev = True
			else :
				#log(revid + ' was a double revision')
				pass

		# finished a page
		if line == '    </revision>\n' :
			if not newtitle : continue
			if before != '' and timestamp > before : continue
			if content == '' : continue
			processedrevisions[int(revid)] = True
			newtitle = False

			if item or property :
				content = content.replace('&quot;', '"')
				val = eval(content)
				if 'label' in val and len(val['label']) > 0 :
					for lang in val['label'].keys() :
						kb.write(title + ' label {' + lang + ':' + val['label'][lang] + "} .\n")
				if 'description' in val and len(val['description']) > 0 :
					for lang in val['description'].keys() :
						kb.write(title + ' description {' + lang + ':' + val['description'][lang] + "} .\n")
				if 'links' in val and len(val['links']) > 0 :
					for lang in val['links'].keys() :
						kb.write(title + ' link {' + lang + ':' + val['links'][lang] + "} .\n")
				if 'aliases' in val and len(val['aliases']) > 0 :
					for lang in val['aliases'].keys() :
						for alias in val['aliases'][lang] :
							kb.write(title + ' alias {' + lang + ':' + alias + "} .\n")

			if item :
				itemcount += 1
				if 'links' in val and len(val['links']) > 0 :
					sitelinkcount += len(val['links'])
					for lang in val['links'].keys() :
						if lang not in langsitelinks :
							langsitelinks[lang] = 0
						langsitelinks[lang] += 1
				if 'label' in val and len(val['label']) > 0 :
					labelcount += len(val['label'])
					for lang in val['label'].keys() :
						if lang not in langlabels :
							langlabels[lang] = 0
						langlabels[lang] += 1
				if 'description' in val and len(val['description']) > 0 :
					descriptioncount += len(val['description'])
					for lang in val['description'].keys() :
						if lang not in langdescriptions :
							langdescriptions[lang] = 0
						langdescriptions[lang] += 1
				if 'claims' in val and len(val['claims']) > 0 :
					hasrefs = False
					for claim in val['claims'] :
						if len(claim['refs']) > 0 :
							refs += len(claim['refs'])
							claimswithrefs += 1
							hasrefs = True
					if hasrefs : itemswithrefs += 1
					itemswithclaims += 1
					claimcount += len(val['claims'])
					numberofclaims = len(val['claims'])
					if not numberofclaims in claimsperitem :
						claimsperitem[numberofclaims] = 0
					if max(claimsperitem) <= numberofclaims :
						titleofmostclaims = title
					claimsperitem[numberofclaims] += 1
				if 'claims' in val and len(val['claims']) > 0 :
					for claim in val['claims'] :
						quals = ''
						if (len(claim['q']) + len(claim['refs'])) > 0 :
							if (len(claim['q']) > 0) :
								for q in claim['q'] :
									quals += '  ' + snaktotext(q) + " ,\n"
							if (len(claim['refs']) > 0) :
								for ref in claim['refs'] :
									quals += "  reference {\n"
									for r in ref :
										quals += '    ' + snaktotext(r) + " ,\n"
									quals += "  },\n"
							quals = " (\n" + quals + ' )'
							
						snak = snaktotext(claim['m'])
						kb.write(title + ' ' + snak + quals + " .\n")

			if property :
				propertycount += 1
				propertylabelcount += len(val['label'])
				propertydescriptioncount += len(val['description'])
				kb.write(title + ' type ' + val['datatype'] + " .\n")

			if not newrev : continue
			revisioncount += 1
			if item:
				itemrevisioncount += 1

		if line.startswith('        <username>') : # TODO does not catch IPs
			if not newrev : continue
			username = line[18:-12]
			users.add(username)
			if username in bots:
				botrevisioncount += 1
				if timestamp not in boteditsperdate :
					boteditsperdate[timestamp] = 0
				boteditsperdate[timestamp] += 1
			else :
				if timestamp not in humaneditsperdate :
					humaneditsperdate[timestamp] = 0
				humaneditsperdate[timestamp] += 1

		if line.startswith('      <timestamp>') :
			timestamp = line[17:-23]

		# checks for anomalies
		if line.startswith('      <text xml:space="preserve">') :
			if item or property :
				if not line.endswith('</text>\n') :
					log(line)
				else :
					content = line[33:-8]

		#if linecount >= 1000000 : break #xxx

kb = open('kb.txt', 'w')

# process the dailies, starting with the newest
files = 0
for daily in reversed(dailies) :
	if daily == stopdaily : break
	log('Analysing daily ' + daily)
	os.chdir('daily' + daily)
	if not os.path.exists('pages-meta-hist-incr.xml.bz2') :
		log('No data available')
		os.chdir('..')
		continue
	file = bz2.BZ2File('pages-meta-hist-incr.xml.bz2')

	if lastdaily == 0 :
		lastdaily = daily
		kb.write('# ' + daily + "\n")
	processfile(file)

	os.chdir('..')

# process the dump
log('Analysing dump ' + str(latestdump))
os.chdir('dump' + latestdump)
file = bz2.BZ2File('pages-meta-history.xml.bz2')
processfile(file)
os.chdir('..')

kb.close()

os.chdir('..')

# if there is no results directory, create one
if not os.path.exists('results') :
	os.makedirs('results')

output = open('results/daily.html', 'w')
output.write('<!doctype html>' + "\n")
output.write('<html>' + "\n")
output.write(' <head>' + "\n")
output.write('  <meta charset="utf-8">' + "\n")
output.write('  <title>Analysis results</title>' + "\n")
output.write('  <link rel="stylesheet" href="analysis.css" />' + "\n")
output.write(' </head>' + "\n")
output.write(' <body>' + "\n")
output.write('  <h1>Analysis results on the Wikidata dump</h1>' + "\n")
output.write('  <p>' + "\n")
output.write('   As of: ' + str(lastdaily) + '<br>' + "\n")
output.write('   Items: ' + str(itemcount) + '<br>' + "\n")
output.write('   Items with claims: ' + str(itemswithclaims) + '<br>' + "\n")
output.write('   Claims: ' + str(claimcount) + '<br>' + "\n")
output.write('   Claims per item: ' + str(claimsperitem) + '<br>' + "\n")
output.write('   References: ' + str(refs) + '<br>' + "\n")
output.write('   Claims with references: ' + str(claimswithrefs) + '<br>' + "\n")
output.write('   Items with references: ' + str(itemswithrefs) + '<br>' + "\n")
output.write('   Item with most claims: ' + titleofmostclaims + '<br>' + "\n")
output.write('   Properties: ' + str(propertycount) + '<br>' + "\n")
output.write('   Links: ' + str(sitelinkcount) + '<br>' + "\n")
output.write('   Links per language: ' + str(langsitelinks) + '<br>' + "\n")
output.write('   Labels: ' + str(labelcount) + '<br>' + "\n")
output.write('   Labels per language: ' + str(langlabels) + '<br>' + "\n")
output.write('   Labels of properties: ' + str(propertylabelcount) + '<br>' + "\n")
output.write('   Descriptions: ' + str(descriptioncount) + '<br>' + "\n")
output.write('   Descriptions per language: ' + str(langdescriptions) + '<br>' + "\n")
output.write('   Descriptions of properties: ' + str(propertydescriptioncount) + '<br>' + "\n")
output.write('   Revisions: ' + str(revisioncount) + '<br>' + "\n")
output.write('   Item revisions: ' + str(itemrevisioncount) + '<br>' + "\n")
output.write('   Bot revisions: ' + str(botrevisioncount) + '<br>' + "\n")
output.write('   Bot edits per date: ' + str(boteditsperdate) + '<br>' + "\n")
output.write('   Human edits per date: ' + str(humaneditsperdate) + '<br>' + "\n")
output.write('   Number of different users: ' + str(len(users)) + '<br>' + "\n")
output.write('   Lines: ' + str(linecount) + '<br>' + "\n")
output.write('   Characters: ' + str(charactercount) + '<br>' + "\n")
output.write('   Time: ' + str(time.time() - start_time) + ' seconds<br>' + "\n")
output.write('  </p>' + "\n")
output.write(' </body>' + "\n")
output.write('</html>' + "\n")
output.close()

log('Done.')

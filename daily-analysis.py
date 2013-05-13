#!/usr/bin/env python2
import sys, bz2, time, gzip, os, urllib, re

def log(txt) :
	print txt

log('Calculating Wikidata stats')

start_time = time.time()

# for dictionary creation
langs = [ 'en', 'de', 'hr', 'uz' ]

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
processedpages = set()
processedrevisions = set()

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
	# check if dump is finished
	dump = urllib.urlopen('http://dumps.wikimedia.org/wikidatawiki/' + date + '/wikidatawiki-' + date + '-pages-meta-history.xml.bz2', 'pages-meta-history.xml.bz2')
	if dump.info().gettype() == "text/html" : dump.close(); continue
	dump.close()
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
	urllib.urlretrieve('http://dumps.wikimedia.org/wikidatawiki/' + latestdump + '/wikidatawiki-' + latestdump + '-pages-meta-history.xml.bz2', 'pages-meta-history.xml.bz2')

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
			urllib.urlretrieve('http://dumps.wikimedia.org/other/incr/wikidatawiki/' + daily + '/wikidatawiki-' + daily + '-pages-meta-hist-incr.xml.bz2', 'pages-meta-hist-incr.xml.bz2')
			log('Done downloading daily ' + daily)
		else :
			log('Daily not done yet - download aborted')
	os.chdir('..')

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

	# General
	global revisioncount
	
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
			if title not in processedpages :
				newtitle = True
				processedpages.add(title)

		if line.startswith('      <id>') :
			revid = line[10:-6]
			if revid not in processedrevisions :
				newrev = True
				processedrevisions.add(revid)

		# finished a page
		if line == '  </page>\n' :
			if not newtitle : continue

			if item or property :
				content = content.replace('&quot;', '"')
				val = eval(content)

			if item :
				itemcount += 1
				if len(val['links']) > 0 :
					sitelinkcount += len(val['links'])
					for lang in val['links'].keys() :
						if lang not in langsitelinks :
							langsitelinks[lang] = 0
						langsitelinks[lang] += 1
				if len(val['label']) > 0 :
					labelcount += len(val['label'])
					for lang in val['label'].keys() :
						if lang not in langlabels :
							langlabels[lang] = 0
						langlabels[lang] += 1
				if len(val['description']) > 0 :
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
						claim = claim['m']
						if claim[0] == 'value' :
							if claim[2] == 'wikibase-entityid' :
								kb.write(title + ' P' + str(claim[1]) + ' Q' + str(claim[3]['numeric-id']) + "\n")
							elif claim[2] == 'string' :
								kb.write(title + ' P' + str(claim[1]) + " '" + claim[3] + "'\n")
						elif claim[0] == 'somevalue' :
							kb.write(title + ' P' + str(claim[1]) + " some\n")
						elif claim[0] == 'novalue' :
							kb.write(title + ' P' + str(claim[1]) + " none\n")
						else :
							log(claim)
							exit()
				if len(val['label']) > 0 :
					for lang in langs :
						if lang in val['label'] :
							dic[lang].write(title + ' ' + val['label'][lang] + "\n")
			if property :
				propertycount += 1
				propertylabelcount += len(val['label'])
				propertydescriptioncount += len(val['description'])

		if line == '    </revision>\n' :
			if not newrev : continue
			revisioncount += 1
			if item:
				itemrevisioncount += 1
		if line.startswith('        <username>') :
			if not newrev : continue
			username = line[18:-12]
			if username in bots:
				botrevisioncount += 1
		if line.startswith('      <timestamp>') :
			timestamp = line[17:-23]

		# checks for anomalies
		if line.startswith('      <text xml:space="preserve">') :
			if item or property :
				if not line.endswith('</text>\n') :
					log(line)
				else :
					content = line[33:-8]
		#if linecount >= 1000000 : break

kb = open('kb.txt', 'w')
dic = dict()
for lang in langs:
	dic[lang] = open('dict-' + lang + '.txt', 'w')

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

	processfile(file)

	os.chdir('..')

# process the dump
log('Analysing dump ' + str(latestdump))
os.chdir('dump' + latestdump)
file = bz2.BZ2File('pages-meta-history.xml.bz2')
processfile(file)
os.chdir('..')

kb.close()
for lang in langs:
	dic[lang].close()

os.chdir('..')

log(str(len(processedpages)) + ' pages')
log(str(itemcount) + ' items')
log(str(itemswithclaims) + ' items with claims')
log(str(claimcount) + ' claims')
log('claims per item ' + str(claimsperitem))
log(str(refs) + ' refs')
log(str(claimswithrefs) + ' claims with refs')
log(str(itemswithrefs) + ' items with refs')
log(str('item with most claims: ' + str(titleofmostclaims))
log(str(propertycount) + ' properties')
log(str(sitelinkcount) + ' links')
log(str(langsitelinks))
log(str(labelcount) + ' labels')
log(str(langlabels))
log(str(propertylabelcount) + 'labels (of properties)')
log(descriptioncount + ' descriptions')
log(str(langdescriptions))
log(str(propertydescriptioncount) + ' descriptions (of properties)')
log(str(revisioncount) + ' revisions')
log(str(itemrevisioncount) + ' revisions of items')
log(str(botrevisioncount) + 'revisions edited by bot')
log(str(linecount) + ' lines')
log(str(charactercount) + ' characters')

log(str(time.time() - start_time) + ' seconds')
log('Done.')

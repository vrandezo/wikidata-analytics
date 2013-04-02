#!/usr/bin/env python2
import sys, bz2, time, gzip, os, urllib, re

print >> sys.stderr, 'Calculating Wikidata stats'

start_time = time.time()

# read the list of bots
print >> sys.stderr, 'Loading list of bots'
bots = []
botsjson = urllib.urlopen('http://www.wikidata.org/w/api.php?action=query&list=allusers&augroup=bot&aulimit=500&format=json').read()
botsjson = eval(botsjson)
for bot in botsjson['query']['allusers'] :
	bots.append(bot['name'])
print >> sys.stderr, 'List of bots:', bots

linecount = 0
charactercount = 0

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
print >> sys.stderr, 'Checking for the date of the last dump'
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
print >> sys.stderr, 'Latest dump has been on', latestdump

# download the latest stats if needed
if not os.path.exists('dump' + latestdump) :
	os.makedirs('dump' + latestdump)
os.chdir('dump' + latestdump)
if not os.path.exists('site_stats.sql.gz') :
	print >> sys.stderr, 'Downloading stats of the latest dump'
	urllib.urlretrieve('http://dumps.wikimedia.org/wikidatawiki/' + latestdump + '/wikidatawiki-' + latestdump + '-site_stats.sql.gz', 'site_stats.sql.gz')
	
# download the latest dump if needed
if not os.path.exists('pages-meta-history.xml.bz2') :
	print >> sys.stderr, 'Downloading latest dump'
	urllib.urlretrieve('http://dumps.wikimedia.org/wikidatawiki/' + latestdump + '/wikidatawiki-' + latestdump + '-pages-meta-history.xml.bz2', 'pages-meta-history.xml.bz2')

# get the maxrevid of the latest dump
maxrevid = 0
for line in gzip.open('site_stats.sql.gz'):
	if not line.startswith('INSERT INTO') : continue
	stats = eval(line[32:-2])
	maxrevid = int(stats[2])
print >> sys.stderr, 'maxrevid of the latest dump:', maxrevid

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
	print >> sys.stderr, 'Checking daily of', daily
	if not os.path.exists('daily' + daily) :
		os.makedirs('daily' + daily)
	os.chdir('daily' + daily)
	if not os.path.exists('maxrevid.txt') :
		urllib.urlretrieve('http://dumps.wikimedia.org/other/incr/wikidatawiki/' + daily + '/maxrevid.txt', 'maxrevid.txt')
	dailymaxrevid = int(open('maxrevid.txt').read())
	if dailymaxrevid < maxrevid :
		print >> sys.stderr, 'Daily', daily, 'is within latest dump'
		stopdaily = daily
		os.chdir('..')
		break
	if not os.path.exists('pages-meta-hist-incr.xml.bz2') :
		print >> sys.stderr, 'Downloading daily', daily
		if urllib.urlopen('http://dumps.wikimedia.org/other/incr/wikidatawiki/' + daily + '/status.txt').read() == 'done' :
			urllib.urlretrieve('http://dumps.wikimedia.org/other/incr/wikidatawiki/' + daily + '/wikidatawiki-' + daily + '-pages-meta-hist-incr.xml.bz2', 'pages-meta-hist-incr.xml.bz2')
			print >> sys.stderr, 'Done downloading daily', daily
		else :
			print >> sys.stderr, 'Daily not done yet - download aborted'
	os.chdir('..')

def processfile(file) :
	global linecount
	global charactercount

	# Items
	global itemcount
	global itemswithclaims
	global claimcount
	global claimsperitem
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
		if linecount % 1000000 == 0 : print >> sys.stderr, linecount / 1000000

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
					itemswithclaims += 1
					claimcount += len(val['claims'])
					numberofclaims = len(val['claims'])
					if not numberofclaims in claimsperitem :
						claimsperitem[numberofclaims] = 0
					if max(claimsperitem) <= numberofclaims :
						titleofmostclaims = title
					claimsperitem[numberofclaims] += 1
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
					print >> sys.stderr, line
				else :
					content = line[33:-8]
		#if linecount >= 1000000 : break

# process the dailies, starting with the newest
files = 0
for daily in reversed(dailies) :
	if daily == stopdaily : break
	print >> sys.stderr, 'Analysing daily', daily
	os.chdir('daily' + daily)
	if not os.path.exists('pages-meta-hist-incr.xml.bz2') :
		print >> sys.stderr, 'No data available'
		os.chdir('..')
		continue
	file = bz2.BZ2File('pages-meta-hist-incr.xml.bz2')

	processfile(file)

	os.chdir('..')

# process the dump
print >> sys.stderr, "Analysing dump", latestdump
os.chdir('dump' + latestdump)
file = bz2.BZ2File('pages-meta-history.xml.bz2')
processfile(file)
os.chdir('..')

os.chdir('..')

print len(processedpages), 'pages'
print itemcount, 'items'
print itemswithclaims, 'items with claims'
print claimcount, 'claims'
print 'claims per item', claimsperitem
print 'item with most claims:', titleofmostclaims
print propertycount, 'properties'
print sitelinkcount, 'links'
print langsitelinks
print labelcount, 'labels'
print langlabels
print propertylabelcount, 'labels (of properties)'
print descriptioncount, 'descriptions'
print langdescriptions
print propertydescriptioncount, 'descriptions (of properties)'
print revisioncount, 'revisions'
print itemrevisioncount, 'revisions of items'
print botrevisioncount, 'revisions edited by bot'
print linecount, 'lines'
print charactercount, 'characters'

print time.time() - start_time, 'seconds'
print >> sys.stderr, 'Done.'

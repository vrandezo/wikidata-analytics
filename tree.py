# create a tree out of a propertyset
# needs the propertyset
import sys

if len(sys.argv) < 2 :
	print 'no property id given'
	exit()
propertyid = sys.argv[1]
if not propertyid.isdigit() :
	print property, 'is not a property id'
	exit()
propertyid = int(propertyid)

output = open('data/P' + str(propertyid) + '-tree.txt', 'w')

tree = dict()
alls = set()
allo = set()
for line in open('data/P' + str(propertyid) + '.txt') :
	if line.startswith('#') :
		output.write(line)
		continue
	s, o = line.strip().split()
	if o not in tree :
		tree[o] = set()
	tree[o].add(s)
	alls.add(s)
	allo.add(o)

roots = set()
for o in allo :
	if o not in alls :
		roots.add(o)

print 's', len(alls)
print 'o', len(allo)
print 'roots', len(roots)

def printnode(node, indent, tree, printed, output) :
	output.write((indent*' ') + node + "\n")
	if node in printed :
		output.write(((indent+1)*' ') + '...' + "\n")
		return
	printed.add(node)
	if node in tree :
		for child in tree[node] :
			printnode(child, indent + 1, tree, printed, output)

for root in roots :
	printnode(root, 0, tree, set(), output)

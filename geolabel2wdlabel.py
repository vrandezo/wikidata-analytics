# -*- coding: UTF-8 -*-
# trafo -> png
import gzip
	
count = 0

output = open('wdlabel.js', 'w')

output.write("var geodata = {\n") 
with gzip.open('geolabel.txt.gz') as f :
	for line in f :
		if line.startswith('#') : continue
		geox, geoy, property, subject, label = line.strip().split(' ', 4)
		label = label.replace('"', '\\"')
		if float(geoy) > 180 or float(geoy) < -180 or float(geox) > 90 or float(geox) < -90 :
			print geoy, geox
			continue
		output.write('  "' + subject + '" : { x : ' + geox + ', y : ' + geoy + ', label : "' + label + '" },' + "\n")

		count += 1
		#if count > 10 : break

output.write('};')
output.close()

print "Finished."

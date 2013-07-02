# trafo -> png
import gzip
	
count = 0

output = open('wd.js', 'w')

output.write("exports.geodata = {\n")

with gzip.open('geo.txt.gz') as f :
	for line in f :
		if line.startswith('#') : continue
		geox, geoy, property, subject = line.split()
		if float(geoy) > 180 or float(geoy) < -180 or float(geox) > 90 or float(geox) < -90 :
			print geoy, geox
			continue
		output.write('  "' + subject + '" : { x : ' + geox + ', y : ' + geoy + " },\n")

		count += 1
		#if count > 10 : break

output.write("};")
output.close()

print "Finished."

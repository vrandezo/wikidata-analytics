# trafo -> png
import png, sys, gzip

settings = {
	'icon' : {
		'x' : 80,
		'y' : 80,
		'diffr' : 80,
		'diffg' : 5,
		'diffb' : 1
	},
	'tiny' : {
		'x' : 500,
		'y' : 250,
		'diffr' : 100,
		'diffg' : 10,
		'diffb' : 2
	},
	'small' : {
		'x' : 1000,
		'y' : 500,
		'diffr' : 100,
		'diffg' : 25,
		'diffb' : 8
	},
	'normal' : {
		'x' : 2000,
		'y' : 1000,
		'diffr' : 150,
		'diffg' : 40,
		'diffb' : 10
	},
	'big' : {
		'x' : 4000,
		'y' : 2000,
		'diffr' : 150,
		'diffg' : 50,
		'diffb' : 10
	},
	'huge' : {
		'x' : 8000,
		'y' : 4000,
		'diffr' : 150,
		'diffg' : 70,
		'diffb' : 20
	}
}
	
for size in settings.keys() :
	print size
	print settings[size]

	p = [[0]*(settings[size]['x'] * 3) for i in range(settings[size]['y'])]

	count = 0

	with gzip.open('geo.txt.gz') as f :
		for line in f :
			geoy, geox, p, s = line.split()
			if float(geox) > 180 or float(geox) < -180 or float(geoy) > 90 or float(geoy) < -90 :
				print geoy, geox
				continue
			geox = int((float(geox) + 180.0)/361.0*settings[size]['x'])
			geoy = abs(int((float(geoy) -  90.0)/181.0*settings[size]['y']))
			p[geoy][geox*3] = min(p[geoy][geox*3]+settings[size]['diffr'], 255)
			p[geoy][geox*3+1] = min(p[geoy][geox*3+1]+settings[size]['diffg'], 255)
			p[geoy][geox*3+2] = min(p[geoy][geox*3+2]+settings[size]['diffb'], 255)

			count += 1
			#if count > 10 : break
		
	print size, "Map ready..."
	print count, "entities"

	f = open('map_' + size + '.png', 'wb')
	w = png.Writer(settings[size]['x'], settings[size]['y'])
	w.write(f, p)
	f.close()

print "Finished."

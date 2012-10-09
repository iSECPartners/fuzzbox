#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import random

# parts of the logic here taken from the DDD fuzzers:
# http://www.digitaldwarf.be/products.html

def randstring():
	thestring = ""
	chance = random.randint(0,8)
	print "using method " + str(chance)
	if chance == 0:
		# try a random length of one random char
		char = chr(random.randint(0,255))
		length = random.randint(0,3000)
		thestring = char * length
		# or a format string
	elif chance == 1:
		thestring = "%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n"
	elif chance == 2:
		# some garbage ascii
		for i in range(random.randint(0,3000)):
			char = '\n'
			while  char == '\n':
				char = chr(random.randint(0,127))
			thestring += char
	elif chance == 3:
		# build up a random string of alphanumerics
		chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
		for i in range(random.randint(0,3000)):
			thestring += random.choice(chars)
	elif chance == 4:
		# maybe something with unicode?
		for i in range(random.randint(0,3000)):
		    thestring += unichr(i)
		# encoded or raw, 50/50
		if random.randint(0,1) == 0:
		    thestring.encode('utf-8')
	elif chance == 5:
		# check for fencepost errors
		thestring = random.randint(-1,1)
	elif chance == 6:
		# try NULLs
		thestring = random.choice(["\x00", "\0"])
	elif chance == 7:
		# Perhaps HTML will show up somewhere, could be
		# interesting
		thestring = "<h1>big and noticeable</h1>"
	elif chance == 8:
		# Some tags contain urls. If they're automatically
		# fetched, that could be of note. Insert your 
		# webserver here, and watch for fetches for
		# that file in the logs.
		thestring = "http://labs.isecpartners.com/fuzzboxtest"
	else:
		thestring += str(random.randint(-5000,5000))

	return thestring

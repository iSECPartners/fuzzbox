#!/usr/local/bin/python
# -*- coding: utf-8 -*-

""" 
Fuzzbox 0.3.1
(C)2007, iSEC Partners Inc.
See LICENSE.txt for details.

https://www.isecpartners.com
"""

import random, shutil, struct, os, time, resource, sys
sys.path.append(os.getcwd() + "/mutagen")
import ogg.vorbis, fuzzwave, mutagen.id3, fuzzaifc, mutagen.flac, mutagen.mp4
from randjunk import randstring
from utils import *
from formats import *
from subprocess import *
from optparse import OptionParser

vcomments = ogg.vorbis.VorbisComment(comments)

totaltags = len(vcomments)

# this is to reset the CRC after mangling of the header.
def ogg_page_checksum_set(page):

    crc_reg = 0

    # This excludes the CRC from being part of the new CRC.
    page = page[0:22] + "\x00\x00\x00\x00" + page[26:]

    for i in range(len(page)):
      crc_reg = ((crc_reg<<8) & 0xffffffff) ^ crc_lookup[((crc_reg >> 24) & 0xff) ^ ord(page[i])]

    # Install the CRC.
    page = page[0:22] + struct.pack('I', crc_reg) + page[26:]
    return page

def fuzz_ogg_tags(vcomments, numtofuzz):
	newtags = vcomments.as_dict()

	for i in range(numtofuzz):
	    manglekey = random.choice(newtags.keys())
	    chance = random.randint(0,5)
	    if chance == 0:
		print "generating garbage tag"
		garbagetag = randstring()
		newtags[str(garbagetag)] = randstring()
	    else:
		print "mangling %d tags"%numtofuzz
		newtags[manglekey] = randstring()
	return newtags

def fuzz_mp3_tags(oldtags, texttags, numtofuzz):

	newtags = oldtags

	print "mangling %d tags"%numtofuzz
	for i in range(numtofuzz):
	    manglekey = random.choice(texttags)
	    # pick a random charset encoding
	    enc = random.randint(0,5)

	    print manglekey
	    try:
		newtags.add(eval("mutagen.id3.%s"%manglekey)(encoding=enc, text=randstring()))
	    except:
		print "failed %s"%manglekey
	return newtags

def fuzz_mp3_frame(sourcefile):
    try:
	f=open(sourcefile, 'rb')
    except IOError:
	print "Can't open source mp3 file."

    # taking a cue from mutagen
    data = f.read(32768)
    frame = data.find("\xff")
    frame_data = struct.unpack(">I", data[frame:frame + 4])[0]

    y = {}
    #### MP3 frame structure
    # sync will always be 11 set bits
    y['01version'] = (frame_data >> 19) & 0x3
    y['02layer'] = (frame_data >> 17) & 0x3
    # we'll always change this to off
    y['03protection'] = (frame_data >> 16) & 0x1
    y['04bitrateindex'] = (frame_data >> 12) & 0xF
    y['05sampfreq'] = (frame_data >> 10) & 0x3
    y['06padding'] = (frame_data >> 9) & 0x1
    y['07private'] = (frame_data >> 8) & 0x1
    y['08channelmode'] = (frame_data >> 6) & 0x3
    y['09modeext'] = (frame_data >> 4) & 0x3
    y['10copyright'] = (frame_data >> 3) & 0x1
    # this is pretty pointless
    y['11original'] = (frame_data >> 2) & 0x1
    y['12emphasis'] = (frame_data >> 0) & 0x3

    headerlength = f.tell()
    restoffile = f.read()
    filelength = len(restoffile)
    f.close()
    thestring = ""
    letsfuzz = random.choice(y.keys())
    print "fuzzing %s"%letsfuzz

    thestring = "%X" % random.randint(0,15)
    y[letsfuzz] = thestring
    print y

    return y, restoffile

def fuzz_ogg_frame(sourcefile):
    try:
	f=open(sourcefile, 'rb')
    except IOError:
	print "Can't open source ogg file."

    y = {}
    #### Ogg structure
    # the magic number
    y['01magic'] = f.read(4)
    # should always be 0x00
    y['02version'] = f.read(1)
    # 0x01 is cont
    # 0x02 is BOS
    # 0x04 is EOS
    y['03headertype'] = f.read(1)
    # a time marker
    y['04granulepos'] = f.read(8)
    # this is stored backwards??
    y['05serial'] = f.read(4)
    # just the number of the page
    y['06pageseq'] = f.read(4)
    # CRC
    y['07crc'] = f.read(4)
    # number of segs in a page
    y['08numsegments'] = f.read(1)
    # umm, not sure
    y['09segtable'] = f.read(1)
    #### Vorbis structure
    # 0x00 is audio packet
    # 0x01 is id packet
    # 0x03 is comment packet
    # 0x05 is setup packet
    y['10packettype'] = f.read(1)
    # always "vorbis"
    y['11streamtype'] = f.read(6)
    # version of vorbis
    y['12version'] = f.read(4)
    # number of audio channels
    y['13channels'] = f.read(1)
    # self explanatory
    y['14samplerate'] = f.read(4)
    y['15maxbitrate'] = f.read(4)
    y['16nominalbitrate'] = f.read(4)
    y['17minbitrate'] = f.read(4)
    # first 4 bits are blocksize_0, next are blocksize_1
    y['18blocksize'] = f.read(1)
    # the framing byte
    y['19framing'] = f.read(1)

    # should be 58 bytes
    headerlength = f.tell()
    restoffile = f.read()
    filelength = len(restoffile)
    f.close()

    thestring = ""
    letsfuzz = random.choice(y.keys())
    print "fuzzing %s"%letsfuzz

    thestring = randstring()
    stringtype = type(thestring)
    length = len(y[letsfuzz])
    if str(stringtype) == "<type 'str'>":
	y[letsfuzz] = struct.pack('s', thestring[:length])
    elif str(stringtype) == "<type 'int'>":
	y[letsfuzz] = struct.pack('i', thestring)
    else:
	thestring = ""
	for i in range(len(y[letsfuzz])):
	    thestring += "%X" % random.randint(0,15)

    return y,restoffile

def fuzz_flac_frame(sourcefile):
    try:
	f=open(sourcefile, 'rb')
    except IOError:
	print "Can't open source flac file."

    y = {}

    ### FLAC structure
    y['01magic'] = f.read(4)
    y['02header'] = f.read(1)
    y['03length'] = f.read(3)
    y['04minblocksize'] = f.read(2)
    y['05maxblocksize'] = f.read(2)
    y['06minframesize'] = f.read(3)
    y['07maxframesize'] = f.read(3)
    y['08samplerate_n_channels'] = f.read(3)

    restoffile = f.read()
    filelength = len(restoffile)
    f.close()

    thestring = ""
    letsfuzz = random.choice(y.keys())
    print "fuzzing %s"%letsfuzz

    thestring = randstring()
    stringtype = type(thestring)
    length = len(y[letsfuzz])
    if str(stringtype) == "<type 'str'>":
	y[letsfuzz] = struct.pack('s', thestring[:length])
    elif str(stringtype) == "<type 'int'>":
	y[letsfuzz] = struct.pack('i', thestring)
    else:
	thestring = ""
	for i in range(len(y[letsfuzz])):
	    thestring += "%X" % random.randint(0,15)
	#untested
	#y[letsfuzz] = thestring

def fuzz_speex_frame(sourcefile):
    try:
	f=open(sourcefile, 'rb')
    except IOError:
	print "Can't open source flac file."

    y = {}

    y['00beginning'] = f.read(28)
    y['01sync'] = f.read(8)
    y['02version'] = f.read(20)
    y['03versionid'] = f.read(4)
    y['04headersize'] = f.read(4)
    y['05rate'] = f.read(4)
    y['06mode'] = f.read(4)
    y['07modebitstreamversion'] = f.read(4)
    y['08nbchannels'] = f.read(4)
    y['09bitrate'] = f.read(4)
    y['10framesize'] = f.read(4)
    y['11vbr'] = f.read(4)
    y['12framesperpacket'] = f.read(4)
    y['13extraheaders'] = f.read(4)
    y['14reserved1'] = f.read(4)
    y['15reserved2'] = f.read(4)

    restoffile = f.read()
    filelength = len(restoffile)
    f.close()

    thestring = ""
    letsfuzz = random.choice(y.keys())
    print "fuzzing %s"%letsfuzz

    thestring = randstring()
    stringtype = type(thestring)
    length = len(y[letsfuzz])
    if str(stringtype) == "<type 'str'>":
	y[letsfuzz] = struct.pack('s', thestring[:length])
    elif str(stringtype) == "<type 'int'>":
	y[letsfuzz] = struct.pack('i', thestring)
    else:
	thestring = ""
	for i in range(len(y[letsfuzz])):
	    thestring += "%X" % random.randint(0,15)
	#untested
	#y[letsfuzz] = thestring

    return y,restoffile

def fuzz_flac_tags(comments, fh, numtofuzz):

	for i in range(numtofuzz):
	    manglekey = random.choice(comments.keys())
	    print manglekey
	    chance = random.randint(0,1)
	    if chance == 0:
		print "generating garbage tag"
		garbagetag = randstring()
		try:
		    fh[str(garbagetag)] = randstring()
		except UnicodeEncodeError: pass	
	    else:
		print "mangling %d tags"%numtofuzz
		fh[manglekey] = randstring()
	return fh

def fuzz_qt_atoms(oldatoms, numtofuzz):

	newatoms = oldatoms

	print "mangling %d tags"%numtofuzz
	for i in range(numtofuzz):
	    manglekey = random.choice(qtatoms)
	    # pick a random charset encoding
	    enc = random.randint(0,5)

	    print manglekey
	    #try:
	    newatoms[manglekey] = randstring()
	    #except:
	#	print "failed %s"%manglekey
	return newatoms

def playit(filename, timeout):
	log = open(logfile, "a")
	gdbfile = open("/tmp/gdbparams", "w") 
	gdbfile.write("set args %s\n"%filename)
	if itunes == True:
	    gdbfile.write("break ptrace if $r3 == 31\n")
	gdbfile.write("run\n")
	gdbfile.write("bt\n")
	if itunes == True:
	    gdbfile.write("return\n")
	    gdbfile.write("cont\n")
	    gdbfile.write("bt\n")
	gdbfile.write("info reg\n")
	gdbfile.write("quit\n")
	gdbfile.close()
	# this is stupid. stdin=None causes the program to suspend
	# when gdb is killed.
	devnull = open("/dev/null", "r")
	log.write("===> Playing %s\n"%filename)
	gdb = Popen(["gdb", "-batch", "-x", "/tmp/gdbparams", progname], stdin=devnull, stdout=log, stderr=log)
	if itunes == True:
	    # give a little time for gdb and iTunes to start up
	    time.sleep(10)
	    os.system("/usr/bin/open -a iTunes %s"%filename)
	x = 0
	# Watch the process to see if it gets stuck - either because
	# of an infinite loop, or because the player doesn't exit when
	# the file is complete. You'll get better performance if you 
	# can make the player exit when done.
	while 1:
	    try:
		if os.waitpid(gdb.pid,os.WNOHANG)[0]==0:
		    time.sleep(1)
		    x = x + 1
		    if x >= timeout:
			print "process still running, killing it"
			log.write("===> Resources: " + str(resource.getrusage(resource.RUSAGE_CHILDREN)) + "\n")
			# Yeah, sorry. Replace with whatever
			# works for you. Hope you weren't listening
			# to something in another instance. :)
			os.system("killall -9 `basename %s`"%progname)
			break
	    except OSError:
		log.write("process died playing %s\n."%filename)
		break

	log.close()

count = 0

def get_options():
    parser = OptionParser(version='%prog version 0.1')

    parser.add_option('-r', '--reps', action='store', dest='reps',
	help='Number of files to generate/play',
	default = 10, type = int)

    parser.add_option('-p', '--program', action='store', dest='progname',
	default = None,
	help='Path to the player you\'d like to test')

    parser.add_option('-l', '--logfile', action='store', dest='logfile',
	help='Path to the logfile to record results',
	default = "playlog.log")

    parser.add_option('-s', '--source', action='store', dest='sourcefile',
	default = None,
	help='Path to a source file to fuzz')

    parser.add_option('-t', '--timeout', action='store', dest='timeout',
	default = 20, type = int,
	help='How long to wait for the player to crash')

    parser.add_option('-n', '--fuzzmax', action='store', dest='fuzzmax',
	default = 5, type = int,
	help='Maximum number of file elements to fuzz')

    parser.add_option('--itunes', action='store_true', dest='itunes',
	default = False,
	help='Work around iTunes anti-debugging')

    parser.add_option('--filetype', action='store', dest='filetype',
	default = "ogg",
	help='Type of file to fuzz: wav, aiff, spx, mp3, mp4 or ogg')


    return parser

# main stuff starts here.
parser = get_options()
(ops, args) = parser.parse_args()
reps = ops.reps
progname = ops.progname
logfile = ops.logfile
sourcefile = ops.sourcefile
timeout = ops.timeout
itunes = ops.itunes
filetype = ops.filetype
fuzzmax = ops.fuzzmax

if sourcefile == None:
    print "ERROR: You need to define at least the source file."
    print
    parser.print_help()
    sys.exit(1)

if filetype == "ogg":

    for i in range(reps):
	check = random.randint(0,2)
	if check == 0:
	    print "fuzzing tags."
	    numtofuzz = random.randint(1,fuzzmax)
	    print "fuzzing %d tags"%numtofuzz

	    newfile = 'output' + str(count) + '.ogg'
	    shutil.copyfile(sourcefile, newfile)
	    try:
		newtags = ogg.vorbis.VorbisComment(fuzz_ogg_tags(vcomments, numtofuzz))
		newtags.write_to(newfile)
	    # ignore conversion breakage
	    except (UnicodeEncodeError, ValueError): pass	
	    count = count + 1

	else:

	    print "fuzzing frame."
	    newfile = 'output' + str(count) + '.ogg'
	    shutil.copyfile(sourcefile, newfile)
	    fout = open(newfile, 'wb')
	    newheader,restoffile = fuzz_ogg_frame(sourcefile)
	    # keys() results are unsorted, so put them back in order
	    page = ""
	    for key in sorted(newheader.keys()):
		page += str(newheader[key])

	    page_with_crc = ogg_page_checksum_set(page)
	    fout.write(page_with_crc)
	    fout.close()
	    fout = open(newfile, 'a')
	    fout.write(restoffile)
	    fout.close()
	    if progname != None:
		print "Playing %s..."%newfile
		try:
		    playit(newfile, timeout)
		except KeyboardInterrupt:
		    print "User interrupted, cleaning up."
		    os.system("killall -9 %s"%progname)
		    sys.exit()
	    count = count + 1

elif filetype == "flac":
    numtags = len(comments)
    for i in range(reps):
	check = random.randint(0,2)
	if check == 0:
	    print "fuzzing tags."
	    numtofuzz = random.randint(1,fuzzmax)
	    print "fuzzing %d tags"%numtofuzz

	    newfile = 'output' + str(count) + '.flac'
	    shutil.copyfile(sourcefile, newfile)

	    fh = mutagen.flac.FLAC(newfile)
	    newfh = fuzz_flac_tags(comments, fh, numtofuzz)

	    try:
		newfh.save()
		if progname != None:
		    print "Playing %s..."%newfile
		    try:
			playit(newfile, timeout)
		    except KeyboardInterrupt:
			print "User interrupted, cleaning up."
			os.system("killall -9 %s"%progname)
			sys.exit()
	    except:
		failed = True
		os.remove(newfile)
	    count = count + 1

elif filetype == "mp3":
    numtags = len(texttags)
    for i in range(reps):
	check = random.randint(0,2)
	if check == 20:
	    print "fuzzing tags."
	    numtofuzz = random.randint(1,fuzzmax)
	    newfile = 'output' + str(count) + '.mp3'
	    shutil.copyfile(sourcefile, newfile)

	    oldtags = mutagen.id3.ID3(newfile)

	    newtags = fuzz_mp3_tags(oldtags, texttags, numtofuzz)
	    failed = False
	    try:
		newtags.save(newfile ,2)
	    except:
		print "Failed to save %s"%newfile
		failed = True
		os.remove(newfile)

	    count = count + 1
	else:
	    print "fuzzing frame."
	    newfile = 'output' + str(count) + '.mp3'
	    shutil.copyfile(sourcefile, newfile)
	    fout = open(newfile, 'wb')
	    newheader,restoffile = fuzz_mp3_frame(sourcefile)
	    page = ""
	    for key in sorted(newheader.keys()):
		page += str(newheader[key])

	    fout.write(page)
	    fout.close()
	    fout = open(newfile, 'a')
	    fout.write(restoffile)
	    fout.close()
	    if progname != None:
		print "Playing %s..."%newfile
		try:
		    playit(newfile, timeout)
		except KeyboardInterrupt:
		    print "User interrupted, cleaning up."
		    os.system("killall -9 %s"%progname)
		    sys.exit()
	    count = count + 1

elif filetype == "wav":

    oldwav = fuzzwave.open(sourcefile, 'rb')
    oldparams = oldwav.getparams()
    print oldparams
    numframes = oldwav.getnframes()
    # shouldn't be a problem given a small wav file
    data = oldwav.readframes(numframes)
    oldwav.close()

    for i in range(reps):
	newfile = 'output' + str(count) + '.wav'
	newwav = fuzzwave.open(newfile, 'wb')
#	this mostly tends to just make things not play.
#	if random.randint(0,2):
#	    print "Fuzzing channels"
#	    newwav.setnchannels(random.randint(-10,10))
#    else:
	newwav.setnchannels(oldwav.getnchannels())
	if random.randint(0,2):
	    print "Fuzzing sampwidth"
	    newwav.setsampwidth(random.randint(-1024,1024))
	else:
	    newwav.setsampwidth(oldwav.getsampwidth())
	if random.randint(0,2):
	    print "Fuzzing framerate"
	    newwav.setframerate(random.randint(-1024,50000))
	else:
	    newwav.setframerate(oldwav.getframerate())
	if random.randint(0,2):
	    print "Fuzzing frame number"
	    newwav.setnframes(random.randint(-1024,50000))
	else:
	    newwav.setnframes(oldwav.getnframes())
	if random.randint(0,10):
	    print "Fuzzing compression type"
	    newwav.setcomptype(randstring(), randstring())
	else:
	    newwav.setcomptype(oldwav.getcomptype(), "lalala")
	print "Writing out data"
	try:
	    newwav.writeframesraw(data)
	# There's potential for some divide-by-zeroes here
	except:
	    print "Failed to write that one out"
	newwav.close()
	if progname != None:
	    print "Playing %s..."%newfile
	    try:
		playit(newfile, timeout)
	    except KeyboardInterrupt:
		print "User interrupted, cleaning up."
		os.system("killall -9 %s"%progname)
		sys.exit()
	count = count + 1

elif filetype == "aiff":

    oldaiff = fuzzaifc.open(sourcefile, 'rb')
    oldparams = oldaiff.getparams()
    print oldparams
    numframes = oldaiff.getnframes()
    # shouldn't be a problem given a small file
    data = oldaiff.readframes(numframes)
    oldaiff.close()

    for i in range(reps):
	newfile = 'output' + str(count) + '.aiff'
	newaiff = fuzzaifc.open(newfile, 'wb')
	if random.randint(0,2):
	    print "Fuzzing channels"
	    newaiff.setnchannels(random.randint(-10,10))
	else:
	    newaiff.setnchannels(oldaiff.getnchannels())
	if random.randint(0,2):
	    print "Fuzzing sampwidth"
	    newaiff.setsampwidth(random.randint(-1024,1024))
	else:
	    newaiff.setsampwidth(oldaiff.getsampwidth())
	if random.randint(0,2):
	    print "Fuzzing framerate"
	    newaiff.setframerate(random.randint(-1024,50000))
	else:
	    newaiff.setframerate(oldaiff.getframerate())
	if random.randint(0,2):
	    print "Fuzzing frame number"
	    newaiff.setnframes(random.randint(-1024,50000))
	else:
	    newaiff.setnframes(oldaiff.getnframes())
	if random.randint(0,10):
	    print "Fuzzing compression type"
	    newaiff.setcomptype(randstring(), randstring())
	else:
	    newaiff.setcomptype(oldaiff.getcomptype(), "lalala")
	print "Writing out data"
	try:
	    newaiff.writeframesraw(data)
	    newaiff.close()
	# There's potential for some divide-by-zeroes here
	except:
	    print "Failed to write that one out"
	if progname != None:
	    print "Playing %s..."%newfile
	    try:
		playit(newfile, timeout)
	    except KeyboardInterrupt:
		print "User interrupted, cleaning up."
		os.system("killall -9 %s"%progname)
		sys.exit()
	count = count + 1

elif filetype == "spx":

    for i in range(reps):
	print "fuzzing frame."
	newfile = 'output' + str(count) + '.spx'
	shutil.copyfile(sourcefile, newfile)
	fout = open(newfile, 'wb')
	newheader,restoffile = fuzz_speex_frame(sourcefile)
	page = ""
	for key in sorted(newheader.keys()):
	    page += str(newheader[key])

	page_with_crc = ogg_page_checksum_set(page)
	fout.write(page_with_crc)
	fout.close()
	fout = open(newfile, 'a')
	fout.write(restoffile)
	fout.close()
	if progname != None:
	    print "Playing %s..."%newfile
	    try:
		playit(newfile, timeout)
	    except KeyboardInterrupt:
		print "User interrupted, cleaning up."
		os.system("killall -9 %s"%progname)
		sys.exit()
	count = count + 1

elif filetype == "mp4":
    numtags = len(qtatoms)
    for i in range(reps):
	check = random.randint(0,2)
	if check == 0:
	    print "fuzzing tags."
	    numtofuzz = random.randint(1,fuzzmax)
	    newfile = 'output' + str(count) + '.mp4'
	    shutil.copyfile(sourcefile, newfile)

	    oldatoms = mutagen.mp4.MP4(newfile)

	    newatoms = fuzz_qt_atoms(oldatoms, numtofuzz)
	    failed = False
	    try:
		newatoms.save()
		if progname != None:
		    print "Playing %s..."%newfile
		    try:
			playit(newfile, timeout)
		    except KeyboardInterrupt:
			print "User interrupted, cleaning up."
			os.system("killall -9 `basename %s`"%progname)
			sys.exit()
	    except:
		print "Failed to save %s"%newfile
		failed = True
		os.remove(newfile)

	    count = count + 1

#!/usr/local/bin/python
# -*- coding: utf-8 -*-

# This is the CRC-setting logic stripped out from fuzzbox, for resetting
# the CRC on manually altered files.

import random, shutil, struct, os, time, resource, sys
import ogg.vorbis
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

def read_ogg_frame(sourcefile):
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
    # TODO - I messed up here, blocksize0 and blocksize1 are 4 bits each,
    # not one byte each
    y['18blocksize'] = f.read(1)
    y['19blocksize'] = f.read(1)
    # then there's the framing bit - but we don't need to touch it

    # should be 58 bytes
    headerlength = f.tell()
    restoffile = f.read()
    filelength = len(restoffile)
    f.close()

    return y,restoffile

count = 0

def get_options():
    parser = OptionParser(version='%prog version 0.1')

    parser.add_option('-s', '--source', action='store', dest='sourcefile',
	default = None,
	help='Path to a source file to fuzz')

    parser.add_option('--filetype', action='store', dest='filetype',
	default = "ogg",
	help='Type of file to fuzz: wav, aiff, spx, mp3, mp4 or ogg')


    return parser

# main stuff starts here.
parser = get_options()
(ops, args) = parser.parse_args()
sourcefile = ops.sourcefile
filetype = ops.filetype

if sourcefile == None:
    print "ERROR: You need to define at least the source file."
    print
    parser.print_help()
    sys.exit(1)

if filetype == "ogg":

    print "writing frame."
    newfile = 'output.ogg'
    shutil.copyfile(sourcefile, newfile)
    fout = open(newfile, 'wb')
    newheader,restoffile = read_ogg_frame(sourcefile)
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

fuzzbox
=======
Fuzzbox 0.3.1

A multi-codec media fuzzing tool.

https://www.isecpartners.com/storage/docs/presentations/iSEC-Thiel-Exposing-Vulnerabilities-Media-Software-Presentation.pdf

_Note: This tool is provided for historical reference, and is not being 
actively maintained. Feel free to fork and/or provide pull requests._

Fuzzbox creates corrupt but structurally valid sound files and
optionally launches them in a player, gathering backtraces and
register information. Also included is a standalone tool to reset
the CRCs of Ogg-contained files after manual corruption.

__NOTICE:__ One of the fuzzing tests tries to insert an HTTP URL to check
for programs attempting to make web requests when processing files.
This goes to labs.isecpartners.com by default. Please change this
if you have privacy concerns.

The spawning/killing of the player will only work on UNIX/OSX or
possibly cygwin, as there's unfortunately no simple cross-platform way
to do it. It shouldn't be hard to modify for Windows, though.

For the vorbis comment header, py-vorbis is required. You will have to
increase the max tag buffer size (tag_buff) in pyvorbisinfo.c before
install for this to work right.

For AIFFs, WAVs, MP3s and MP4s, the included Makefile should auto-fetch
and patch the appropriate files. It will need to be edited to know about
your system layout and file transfer program of choice.

You should verify that the mutagen distfile matches this SHA256:

SHA256 (./mutagen-1.11.tar.gz) = 
f22d0570a0d7d1b3d7a54bc70471fe212bd84aaabe5ab1d0c685f2b92a85b11a


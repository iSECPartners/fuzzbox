FETCH_CMD=	fetch
PY_LIB=		/usr/local/lib/python2.5
MUTAGEN_SITE=	http://www.sacredchao.net/~piman/software/
MUTAGEN_DIST=	mutagen-1.11

all: fetch extract patch

fetch:
	${FETCH_CMD} ${MUTAGEN_SITE}${MUTAGEN_DIST}.tar.gz

extract: fetch
	tar -xvzf ${MUTAGEN_DIST}.tar.gz
	mkdir mutagen
	cp -r ${MUTAGEN_DIST}/mutagen/* mutagen/

patch:	extract
	patch -o fuzzwave.py ${PY_LIB}/wave.py < diffs/fuzzwave.py.diff	
	patch -o fuzzaifc.py ${PY_LIB}/aifc.py < diffs/fuzzaifc.py.diff	
	patch mutagen/_vorbis.py < diffs/_vorbis.py.diff
	patch mutagen/id3.py < diffs/id3.py.diff
	patch mutagen/mp4.py < diffs/mp4.py.diff

clean:
	rm -rf aifc.* wave.* mutagen* *.orig *.pyc output* fuzzwave.py \
	fuzzaifc.py
	

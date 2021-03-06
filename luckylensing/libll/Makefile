# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

CFLAGS_ALWAYS = -std=c99 -pedantic -Wall -Wextra -Winline -Wno-uninitialized -fPIC

CFLAGS_OPTIMISE = -O3 -ffinite-math-only -fno-tree-vectorize

# Optimise for the current architecture.  This might make the binary
# unsuitable for use on an inhomogeneous set of machines.  Note that
# floating point to integer conversions are considerably faster with
# sse3, so parts of the lib will perform rather poorly on architectures
# that don't support this extension.
CFLAGS_ARCH = -march=native

CFLAGS = $(CFLAGS_ALWAYS) $(CFLAGS_OPTIMISE) $(CFLAGS_ARCH)

LDLIBS = -lm

default: optimised

all: libll.so testll

testll.o ll.o: ll.h

libll.so: LDFLAGS += -shared
libll.so: ll.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

testll: testll.o ll.o

#####################

profile: CFLAGS += -fprofile-generate
profile: LDFLAGS += -fprofile-generate
profile: clean testll
	./testll

#####################

optimised: profile
	$(MAKE) clean_objects optimised_all

optimised_all: CFLAGS += -fprofile-use
optimised_all: LDFLAGS += -fprofile-use
optimised_all: all

#####################

debug: CFLAGS = $(CFLAGS_ALWAYS) -g
debug: clean all

#####################

clean_objects:
	rm -f ll.o libll.so testll.o testll
	rm -f luckylensing.pyc magpattern.pyc convolve.pyc
	rm -f luckylensing.pyo magpattern.pyo convolve.pyo

clean_profile:
	rm -f ll.gcda ll.gcno testll.gcda testll.gcno

clean: clean_objects clean_profile

.PHONY: all clean clean_objects clean_profile debug default optimised optimised_all profile

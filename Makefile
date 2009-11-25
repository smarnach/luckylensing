# lucky lens Makefile

CFLAGS_ALWAYS = -std=c99 -pedantic -Wall -Wextra -Winline

CFLAGS_OPTIMISE = -O3 -ffinite-math-only

CFLAGS_ARCH = -msse3

CFLAGS = $(CFLAGS_ALWAYS) $(CFLAGS_OPTIMISE) $(CFLAGS_ARCH)

LDLIBS = -lm

default: libll.so

all: default testll

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
	rm -f luckylens.pyc magpattern.pyc convolve.pyc

clean_profile:
	rm -f ll.gcda ll.gcno testll.gcda testll.gcno

clean: clean_objects clean_profile

.PHONY: all clean clean_objects clean_profile debug default optimised optimised_all profile

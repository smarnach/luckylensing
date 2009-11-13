# lucky lens Makefile

CFLAGS = -std=c99 -pedantic -Wall -Wextra -Winline \
         -O3 -funroll-loops -fexpensive-optimizations -ffinite-math-only
#  (Note: -fexpensive-optimizations should be implied by -O3, but it
#   yields consistently slightly faster results on my system when also
#   -funroll-loops is given)

LDLIBS = -lm

default: libll.so

all: default testll

testll.o ll.o: ll.h

libll.so: LDFLAGS += -shared
libll.so: ll.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

testll: testll.o ll.o

clean:
	rm -f ll.o libll.so testll.o testll luckylens.pyc

.PHONY: all clean default

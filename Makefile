CFLAGS = -std=c99 -pedantic -O3 -Wall -Wextra -Winline \
         -funroll-loops -fexpensive-optimizations
# Note: -fexpensive-optimizations should be implied by -O3, but it
# yields consistently slightly faster results on my system when also
# -funroll-loops is given
LDFLAGS =
LIBS = -lm

libll.so: ll.o
	$(CC) -o $@ $(LDFLAGS) -shared $+ $(LIBS)

testll: testll.o
	$(CC) -o $@ $(LDFLAGS) $+ $(LIBS)

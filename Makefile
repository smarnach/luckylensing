CFLAGS = -std=c99 -O2 -Wall
LDFLAGS =
LIBS = -lm

libll.so: ll.o
	$(CC) -o $@ $(LDFLAGS) -shared $+ $(LIBS)

testll: testll.o
	$(CC) -o $@ $(LDFLAGS) $+ $(LIBS)

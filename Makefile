CFLAGS = -std=c99 -O2 -Wall
LDFLAGS = -shared
LIBS = -lm

libll.so: ll.o
	$(CC) -o $@ $(LDFLAGS) $+ $(LIBS)

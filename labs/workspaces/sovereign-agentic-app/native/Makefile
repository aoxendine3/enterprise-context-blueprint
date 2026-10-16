# MTPO Native Engine & Tooling Build
CC ?= clang
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -pthread
LDFLAGS ?= -pthread

all: libmtpo_engine.dylib mtpo_tool

libmtpo_engine.dylib: ../../mtpo/src/mtpo_saga.c ../../mtpo/src/mtpo_saga.h
	$(CC) $(CFLAGS) -shared -fPIC -install_name @rpath/libmtpo_engine.dylib ../../mtpo/src/mtpo_saga.c -o libmtpo_engine.dylib

mtpo_tool: mtpo_tool.c libmtpo_engine.dylib
	$(CC) $(CFLAGS) mtpo_tool.c -L. -lmtpo_engine -Wl,-rpath,@executable_path -o mtpo_tool

clean:
	rm -f libmtpo_engine.dylib mtpo_tool

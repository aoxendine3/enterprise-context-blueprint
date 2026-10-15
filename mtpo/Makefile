CC ?= clang
CFLAGS ?= -Wall -Wextra -Werror -O3 -pthread -std=c11
TARGET = bin/mtpo_test

SRCS = src/mtpo_saga.c tests/test_mtpo_concurrency.c

all: $(TARGET)

$(TARGET): $(SRCS)
	@mkdir -p bin
	$(CC) $(CFLAGS) -o $(TARGET) $(SRCS)

test: $(TARGET)
	@./$(TARGET)

clean:
	rm -rf bin

.PHONY: all test clean

CC ?= clang
CFLAGS ?= -Wall -Wextra -Werror -O3 -pthread -std=c11
TARGET = bin/mtpo_test

SRCS = src/mtpo_saga.c tests/test_mtpo_concurrency.c

all: $(TARGET)

$(TARGET): $(SRCS)
	@mkdir -p bin
	$(CC) $(CFLAGS) -o $(TARGET) $(SRCS)

test: $(TARGET)
	@echo "=== [1/2] Bare-Metal C11 Concurrency Stress Test ==="
	@./$(TARGET)
	@echo "=== [2/2] Upstream Z3 Formal Pre-Order Invariant Audit ==="
	@python3 -m unittest discover -s tests -v

clean:
	rm -rf bin

.PHONY: all test clean

CC = x86_64-elf-gcc
LD = x86_64-elf-ld
CFLAGS = -Wall -Wextra -O2 -ffreestanding -fno-stack-protector -fno-stack-check -fno-lto -m64 -march=x86-64 -mno-80387 -mno-mmx -mno-sse -mno-sse2 -mno-red-zone -mcmodel=kernel
LDFLAGS = -nostdlib -static --no-dynamic-linker -z text -z max-page-size=0x1000 -T linker.ld

OBJS = kernel.o serial.o gdt.o idt.o

kernel.elf: $(OBJS)
	$(LD) $(OBJS) $(LDFLAGS) -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o kernel.elf

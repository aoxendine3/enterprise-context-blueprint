#include <stdint.h>
#include <stddef.h>
#include "limine.h"

extern void init_serial();
extern void print_serial(const char* str);
extern void gdt_init();
extern void idt_init();

// The Limine requests can be placed anywhere, but it is important that
// the compiler does not optimise them away, so, usually, they should
// be made volatile or equivalent.

__attribute__((used, section(".requests")))
static volatile LIMINE_BASE_REVISION(1);

__attribute__((used, section(".requests")))
static volatile struct limine_framebuffer_request framebuffer_request = {
    .id = LIMINE_FRAMEBUFFER_REQUEST,
    .revision = 0
};

// The following will be our kernel's entry point.
// If renaming _start() to something else, make sure to change the
// linker script accordingly.
void _start(void) {
    // Ensure the bootloader actually understands our base revision (see spec).
    if (LIMINE_BASE_REVISION_SUPPORTED == false) {
        for (;;) {
            __asm__("hlt");
        }
    }

    init_serial();
    gdt_init();
    idt_init();

    print_serial("[XORAS::OS] Kernel successfully booted via Limine.\n");

    // We're done, just halt...
    for (;;) {
        __asm__("hlt");
    }
}

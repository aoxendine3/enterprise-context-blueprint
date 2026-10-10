#include <stdint.h>

extern void print_serial(const char* str);

struct idt_entry {
    uint16_t base_lo;
    uint16_t sel;
    uint8_t always0;
    uint8_t flags;
    uint16_t base_mid;
    uint32_t base_hi;
    uint32_t reserved;
} __attribute__((packed));

struct idt_ptr {
    uint16_t limit;
    uint64_t base;
} __attribute__((packed));

struct idt_entry idt[256];
struct idt_ptr idtp;

void idt_set_gate(uint8_t num, uint64_t base, uint16_t sel, uint8_t flags) {
    idt[num].base_lo = base & 0xFFFF;
    idt[num].base_mid = (base >> 16) & 0xFFFF;
    idt[num].base_hi = (base >> 32) & 0xFFFFFFFF;
    idt[num].sel = sel;
    idt[num].always0 = 0;
    idt[num].flags = flags | 0x60; // present, ring 0
    idt[num].reserved = 0;
}

void isr_handler() {
    print_serial("[XORAS::OS] Exception caught! Halting.\n");
    for (;;) __asm__("hlt");
}

extern void isr0();
__asm__ (
".global isr0\n"
"isr0:\n"
"    call isr_handler\n"
"    iretq\n"
);

void idt_init() {
    idtp.limit = (sizeof(struct idt_entry) * 256) - 1;
    idtp.base = (uint64_t)&idt;

    // Set first 32 as basic exception handlers
    for (int i = 0; i < 32; i++) {
        idt_set_gate(i, (uint64_t)isr0, 0x08, 0x8E);
    }

    __asm__ volatile ("lidt %0" : : "m"(idtp));
    __asm__ volatile ("sti");
}

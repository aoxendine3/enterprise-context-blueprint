.data
.align 4
msg:
    .asciz "[SOVRA BARE METAL SAGA KERNEL EXECUTION COMPLETE]\n"

.text
.global _sovrac_gate_sanitizer
.align 4
_sovrac_gate_sanitizer:
    ret

.global _main
.align 4
_main:
    stp x29, x30, [sp, #-32]!
    mov x29, sp

    ldr x0, [sp, #16]
    bl _sovrac_gate_sanitizer
    str x0, [sp, #24]

    // Set loop counter for benchmark
    mov x0, #10
    str x0, [sp, #48]

.L_loop_head_1:
    ldr x0, [sp, #48]
    cmp x0, #0
    b.le .L_loop_exit_1

    // Print message syscall
    mov x0, #1
    adrp x1, msg@PAGE
    add x1, x1, msg@PAGEOFF
    mov x2, #51
    mov x16, #4
    svc #0x80

    // Decrement counter
    ldr x0, [sp, #48]
    sub x0, x0, #1
    str x0, [sp, #48]

    b .L_loop_head_1
.L_loop_exit_1:

    mov x0, #0
    ldp x29, x30, [sp], #32
    ret

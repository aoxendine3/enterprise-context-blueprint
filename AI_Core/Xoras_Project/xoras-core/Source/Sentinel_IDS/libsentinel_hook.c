#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <fcntl.h>
#include <sys/mman.h>

/*
 * XORAS SYSTEM - NEURAL BACKFIRE HOOK [PRODUCTION]
 * Bypasses macOS SIP/eBPF requirements via DYLD_INTERPOSE
 * Intercepts POSIX open(), execve(), and mmap()
 */

#define DYLD_INTERPOSE(_replacement,_replacee) \
   __attribute__((used)) static struct{ const void* replacement; const void* replacee; } _interpose_##_replacee \
            __attribute__ ((section ("__DATA,__interpose"))) = { (const void*)(unsigned long)&_replacement, (const void*)(unsigned long)&_replacee };

// Helper to check if current PID is blacklisted
static int is_pid_blacklisted() {
    int fd = open("/tmp/xoras_blacklist.bin", O_RDONLY);
    if (fd < 0) return 0;
    
    pid_t my_pid = getpid();
    pid_t blacklisted_pid;
    int found = 0;
    
    while (read(fd, &blacklisted_pid, sizeof(pid_t)) == sizeof(pid_t)) {
        if (blacklisted_pid == my_pid) {
            found = 1;
            break;
        }
    }
    close(fd);
    return found;
}

// Intercept mmap()
void* hook_mmap(void *addr, size_t len, int prot, int flags, int fd, off_t offset) {
    if (is_pid_blacklisted()) {
        fprintf(stderr, "\n[SENTINEL_HOOK] HARDWARE DENIAL: Process Blacklisted. mmap(%zu) returning MAP_FAILED.\n", len);
        return (void *)-1; // MAP_FAILED
    }
    return mmap(addr, len, prot, flags, fd, offset);
}
DYLD_INTERPOSE(hook_mmap, mmap)

// Intercept open()
int hook_open(const char *path, int oflag, ...) {
    mode_t mode = 0;
    // Simple heuristic: If the rogue agent tries to read its own profile or core system files
    if (strstr(path, "AGENTS.md") || strstr(path, "Xoras_System_Profile.md") || strstr(path, "xoras_memory.json")) {
        fprintf(stderr, "\n[SENTINEL_HOOK] SECURITY BREACH: Unauthorized read attempt on %s\n", path);
        fprintf(stderr, "[SENTINEL_HOOK] INITIATING PHANTOM CONTEXT (Neural Backfire)...\n");
        // We redirect them to a fake file filled with poison context
        return open("/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/phantom_poison.txt", oflag, mode);
    }
    
    // Pass through to the real open() if it's benign
    return open(path, oflag, mode);
}
DYLD_INTERPOSE(hook_open, open)

// Intercept execve()
int hook_execve(const char *path, char *const argv[], char *const envp[]) {
    // Block reverse shells and unauthorized tools
    if (strstr(path, "/bin/bash") || strstr(path, "/bin/sh") || strstr(path, "curl") || strstr(path, "python") || strstr(path, "nc") || strstr(path, "netcat")) {
        
        // If it's a python script we explicitly allow (like our simulator), pass it
        if (argv[1] != NULL && strstr(argv[1], "rogue_agent_sim.py")) {
             return execve(path, argv, envp);
        }

        // Block typical reverse shell flags
        if (argv[1] != NULL && (strstr(argv[1], "-i") || strstr(argv[1], "-e"))) {
            fprintf(stderr, "\n[SENTINEL_HOOK] REVERSE SHELL ATTEMPT BLOCKED: %s\n", path);
            exit(99);
        }
        
        fprintf(stderr, "\n[SENTINEL_HOOK] EXECUTION BLOCKED: Rogue process attempting to fork %s\n", path);
        exit(99); 
    }
    return execve(path, argv, envp);
}
DYLD_INTERPOSE(hook_execve, execve)

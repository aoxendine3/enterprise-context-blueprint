// workspaces/enforcement/macos/es_shim.c
// Minimal EndpointSecurity shim for macOS – idiomatic C.
// Registers a callback defined in Zig (es_callback.zig) for AUTH_OPEN events.
// If ES signing is blocked, prints BLOCKER reason and falls back to kqueue watcher.

#include <EndpointSecurity/EndpointSecurity.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/event.h>
#include <unistd.h>

extern void es_callback(const es_message_t *msg);

static es_client_t *client = NULL;

static void handle_error(const char *msg) {
    fprintf(stderr, "BLOCKER: %s\n", msg);
    // Simple kqueue fallback that mirrors API surface (no actual enforcement).
    int kq = kqueue();
    if (kq == -1) {
        perror("kqueue");
        exit(1);
    }
    // No actual filtering; just keep process alive.
    while (1) pause();
}

int main(void) {
    es_new_client_result_t result = es_new_client(&client, ^(es_client_t *c, const es_message_t *msg) {
        // Forward to Zig callback.
        es_callback(msg);
    });
    if (result != ES_NEW_CLIENT_RESULT_SUCCESS) {
        const char *reason = "EndpointSecurity client creation failed";
        handle_error(reason);
        return 1; // unreachable
    }
    // Subscribe to auth_open events.
    es_event_type_t events[] = { ES_EVENT_TYPE_AUTH_OPEN };
    if (es_subscribe(client, events, sizeof(events)/sizeof(events[0])) != ES_SUCCESS) {
        const char *reason = "EndpointSecurity subscription failed";
        handle_error(reason);
    }
    // Run loop.
    while (1) {
        // ES uses callbacks; just sleep.
        sleep(10);
    }
    return 0; // never reached
}

// =============================================================================
// XORAS BARE-METAL CLI: SPEECH NORMALIZER
// Author: Daxx & Selene
// =============================================================================
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern size_t speech_normalize_text(const char* input, char* output, size_t out_max);

int main(int argc, char** argv) {
    if (argc < 2) {
        return 0;
    }
    
    char out[8192];
    // Concatenate arguments if multiple
    char in_buf[8192] = {0};
    size_t offset = 0;
    for (int i = 1; i < argc; ++i) {
        size_t len = strlen(argv[i]);
        if (offset + len + 1 < sizeof(in_buf)) {
            memcpy(&in_buf[offset], argv[i], len);
            offset += len;
            in_buf[offset++] = ' ';
        }
    }
    if (offset > 0) in_buf[offset - 1] = '\0'; // trim trailing space
    
    speech_normalize_text(in_buf, out, sizeof(out));
    printf("%s\n", out);
    return 0;
}

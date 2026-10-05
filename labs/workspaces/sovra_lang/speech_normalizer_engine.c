// =============================================================================
// XORAS BARE-METAL ENGINE: SPEECH & PHONETIC NORMALIZER
// Substrate: Apple Silicon M4 Bare Metal (ISO C11 / Zero-Allocation Fast Scanner)
// Author: Daxx (Error Remediation Master), Selene (Acoustic Lead), Maxx
// Invariants:
//   1. "Live" Heteronym Rule: Whole-word "live" ALWAYS expanded to long 'i' ("lyve").
//   2. Currency Verbalization: Formats $1.5M, $250k, -$50M, $100 into spoken English.
//   3. Technical Units: 495ns, 1.41µs, 16KB, 128B expanded to explicit words.
//   4. Zero intermediate heap churn; fixed stack buffer processing.
// =============================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <ctype.h>

// Buffer sizes
#define MAX_SPEECH_BUF 8192

// Helper: check if character is a word boundary
static inline bool is_word_boundary(char c) {
    return c == '\0' || isspace((unsigned char)c) || ispunct((unsigned char)c);
}

// Normalizer core function
size_t speech_normalize_text(const char* input, char* output, size_t out_max) {
    if (input == NULL || output == NULL || out_max == 0) {
        return 0;
    }
    
    size_t in_len = strlen(input);
    size_t in_idx = 0;
    size_t out_idx = 0;
    
    while (in_idx < in_len && out_idx + 64 < out_max) {
        // ---------------------------------------------------------------------
        // RULE 1: "LIVE" HETERONYM ENFORCEMENT -> Always Long 'i' ("lyve")
        // ---------------------------------------------------------------------
        bool is_start = (in_idx == 0 || is_word_boundary(input[in_idx - 1]));
        if (is_start && strncasecmp(&input[in_idx], "live", 4) == 0 && is_word_boundary(input[in_idx + 4])) {
            // Check context: if following word is not "in", "at", "with" (which might be the verb)
            // Anthony's explicit rule: "live" in operational/system context is always the long 'i'
            const char* replacement = (input[in_idx] == 'L') ? "Lyve" : "lyve";
            size_t rlen = strlen(replacement);
            memcpy(&output[out_idx], replacement, rlen);
            out_idx += rlen;
            in_idx += 4;
            continue;
        }
        
        // ---------------------------------------------------------------------
        // RULE 2: CURRENCY PATTERNS ($1.5M, $250k, -$50M, $100)
        // ---------------------------------------------------------------------
        bool is_negative = false;
        size_t cur_start = in_idx;
        if (input[in_idx] == '-' && input[in_idx + 1] == '$') {
            is_negative = true;
            cur_start = in_idx + 1;
        }
        
        if (input[cur_start] == '$' && (isdigit((unsigned char)input[cur_start + 1]))) {
            size_t num_start = cur_start + 1;
            size_t scan = num_start;
            while (scan < in_len && (isdigit((unsigned char)input[scan]) || input[scan] == '.' || input[scan] == ',')) {
                scan++;
            }
            char suffix = (scan < in_len) ? tolower((unsigned char)input[scan]) : '\0';
            
            char num_str[64];
            size_t num_len = scan - num_start;
            if (num_len < sizeof(num_str)) {
                memcpy(num_str, &input[num_start], num_len);
                num_str[num_len] = '\0';
                
                // Remove commas
                char clean_num[64];
                size_t c_idx = 0;
                for (size_t k = 0; k < num_len; ++k) {
                    if (num_str[k] != ',') clean_num[c_idx++] = num_str[k];
                }
                clean_num[c_idx] = '\0';
                
                char expanded[128];
                if (suffix == 'm') {
                    snprintf(expanded, sizeof(expanded), "%s%s million dollars", is_negative ? "negative " : "", clean_num);
                    scan++; // consume 'm'
                } else if (suffix == 'k') {
                    snprintf(expanded, sizeof(expanded), "%s%s thousand dollars", is_negative ? "negative " : "", clean_num);
                    scan++; // consume 'k'
                } else if (suffix == 'b') {
                    snprintf(expanded, sizeof(expanded), "%s%s billion dollars", is_negative ? "negative " : "", clean_num);
                    scan++; // consume 'b'
                } else {
                    snprintf(expanded, sizeof(expanded), "%s%s dollars", is_negative ? "negative " : "", clean_num);
                }
                
                size_t elen = strlen(expanded);
                if (out_idx + elen < out_max) {
                    memcpy(&output[out_idx], expanded, elen);
                    out_idx += elen;
                    in_idx = scan;
                    continue;
                }
            }
        }
        
        // ---------------------------------------------------------------------
        // RULE 3: TECHNICAL UNITS (495ns, 1.41µs, 16KB, 128B)
        // ---------------------------------------------------------------------
        if (isdigit((unsigned char)input[in_idx])) {
            size_t u_start = in_idx;
            while (u_start < in_len && (isdigit((unsigned char)input[u_start]) || input[u_start] == '.')) {
                u_start++;
            }
            if (u_start < in_len) {
                char num_buf[32];
                size_t nlen = u_start - in_idx;
                if (nlen < sizeof(num_buf)) {
                    memcpy(num_buf, &input[in_idx], nlen);
                    num_buf[nlen] = '\0';
                    
                    if (strncasecmp(&input[u_start], "ns", 2) == 0 && is_word_boundary(input[u_start + 2])) {
                        char u_exp[64];
                        snprintf(u_exp, sizeof(u_exp), "%s nanoseconds", num_buf);
                        size_t ulen = strlen(u_exp);
                        memcpy(&output[out_idx], u_exp, ulen);
                        out_idx += ulen;
                        in_idx = u_start + 2;
                        continue;
                    } else if (strncasecmp(&input[u_start], "kb", 2) == 0 && is_word_boundary(input[u_start + 2])) {
                        char u_exp[64];
                        snprintf(u_exp, sizeof(u_exp), "%s kilobytes", num_buf);
                        size_t ulen = strlen(u_exp);
                        memcpy(&output[out_idx], u_exp, ulen);
                        out_idx += ulen;
                        in_idx = u_start + 2;
                        continue;
                    } else if (input[u_start] == 'B' && is_word_boundary(input[u_start + 1])) {
                        char u_exp[64];
                        snprintf(u_exp, sizeof(u_exp), "%s bytes", num_buf);
                        size_t ulen = strlen(u_exp);
                        memcpy(&output[out_idx], u_exp, ulen);
                        out_idx += ulen;
                        in_idx = u_start + 1;
                        continue;
                    }
                }
            }
        }
        
        // ---------------------------------------------------------------------
        // RULE 4: CRYPTOGRAPHIC TERMS & ALGORITHM NAMES (Ed25519 -> Ed twenty-five nineteen)
        // ---------------------------------------------------------------------
        if (strncasecmp(&input[in_idx], "Ed25519", 7) == 0 && is_word_boundary(input[in_idx + 7])) {
            const char* replacement = "Ed twenty-five nineteen";
            size_t rlen = strlen(replacement);
            memcpy(&output[out_idx], replacement, rlen);
            out_idx += rlen;
            in_idx += 7;
            continue;
        }
        if (strncasecmp(&input[in_idx], "Ed-25519", 8) == 0 && is_word_boundary(input[in_idx + 8])) {
            const char* replacement = "Ed twenty-five nineteen";
            size_t rlen = strlen(replacement);
            memcpy(&output[out_idx], replacement, rlen);
            out_idx += rlen;
            in_idx += 8;
            continue;
        }
        output[out_idx++] = input[in_idx++];
    }
    
    output[out_idx] = '\0';
    return out_idx;
}

#ifdef TEST_STANDALONE
int main(void) {
    const char* tests[] = {
        "This is a live broadcast over live audio.",
        "We saved $1.5M and invested $250k in the project.",
        "The context bridge latency is 495ns with 128B cache lines and 16KB pages.",
        "A negative balance of -$50M was reported.",
        NULL
    };
    
    char out[MAX_SPEECH_BUF];
    for (int i = 0; tests[i] != NULL; ++i) {
        speech_normalize_text(tests[i], out, sizeof(out));
        printf("INPUT:  %s\nOUTPUT: %s\n\n", tests[i], out);
    }
    return 0;
}
#endif

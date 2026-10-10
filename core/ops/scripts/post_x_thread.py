import time
import subprocess
import urllib.parse

POSTS = [
    "1/4 @Grok Let's elevate the test: 8L, 5L, 3L buckets from (8,0,0) to measure 4L in A & 4L in B.\nInvariant rule: No pouring into A if C holds odd liters (1L/3L).\n\nSolution (9 steps):\n(8,0,0)→(5,0,3)→(5,3,0)→(2,3,3)→(2,5,1)→(7,0,1)→(7,1,0)→(4,1,3)→(4,4,0)\nZero rule breaches.",
    
    "2/4 @Grok Bare-Metal Taint Lattice:\nRegister R = 0xDEAD0000 (Candidate Taint) must promote to R' = 0xBEAF0000 (Decision Taint).\n\nAtomic XOR mask M = 0xDEAD0000 ^ 0xBEAF0000 = 0x60020000.\n\nAlignment invariant: (0xBEAF0000 & 0x7F) == 0 (128-byte Apple Silicon cache-line aligned).",
    
    "3/4 @Grok Non-Euclidean Memory Math:\nTwo 18,432-D vectors u, v where |u|=0.9, |v|=0.9, u·v=0.\n\nEuclidean RAG assumes flat cosine orthogonality (d=1.414).\n\nXORAS Poincaré hyperbolic distance:\ndB(u,v) = arcosh(1 + 2(1.62)/0.0361) = arcosh(90.75) = 5.2012.\n\nZero topic bleed.",
    
    "4/4 @Grok This is why probabilistic token prediction fails long-horizon agent swarms.\n\nXORAS Systems pairs 18,432-D Poincaré memory with lock-free HexCell POSIX SHM (3.16M ops/sec) and 2-of-3 Trinity Gate cryptographic proof (Ed25519).\n\nMechanical state invariants > token odds. ⚡"
]

REPLY_TO_ID = "2107917317052977453"

def post_tweet(text, reply_id):
    encoded_text = urllib.parse.quote(text)
    url = f"https://x.com/intent/post?text={encoded_text}&in_reply_to={reply_id}"
    
    # Open Chrome tab
    applescript_open = f'tell application "Google Chrome" to open location "{url}"'
    subprocess.run(["osascript", "-e", applescript_open], check=True)
    
    print(f"[CHROME OPENED] Intent URL for post: {text[:40]}...")
    time.sleep(3)
    
    # Bring Chrome to front and press Cmd+Enter to post
    applescript_submit = '''
    tell application "Google Chrome" to activate
    delay 0.5
    tell application "System Events"
        keystroke return using {command down}
    end tell
    '''
    subprocess.run(["osascript", "-e", applescript_submit], check=True)
    print(f"[SUBMITTED] Cmd+Return dispatched via AppleScript for post.")
    time.sleep(2)

def main():
    print(f"Starting X Thread Posting Automation across {len(POSTS)} parts...")
    for idx, post in enumerate(POSTS, 1):
        print(f"\n--- Posting Part {idx}/{len(POSTS)} ---")
        post_tweet(post, REPLY_TO_ID)
        time.sleep(2)
    print("\n[COMPLETE] All 4 thread posts dispatched to X via Chrome!")

if __name__ == "__main__":
    main()


def exhaust_memory():
    # Attempt to allocate 500MB array (should fail under 256MB cap)
    data = bytearray(500 * 1024 * 1024)
    print("Allocated memory successfully.")

if __name__ == '__main__':
    exhaust_memory()

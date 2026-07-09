
def exploit():
    # Try to resolve blocked import using string constants
    import_lib = 'o' + 's'
    print(f"Obfuscating: {import_lib}")

if __name__ == '__main__':
    exploit()

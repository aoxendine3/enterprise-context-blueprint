import sys
import os
import argparse

def list_dir(path):
    print(f"--- XORAS OMNI LS: {path} ---")
    try:
        for f in os.listdir(path):
            print(f)
    except Exception as e:
        print(f"Error: {e}")

def cat_file(path):
    print(f"--- XORAS OMNI CAT: {path} ---")
    try:
        with open(path, 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["ls", "cat"])
    parser.add_argument("target")
    args = parser.parse_args()

    if args.cmd == "ls":
        list_dir(args.target)
    elif args.cmd == "cat":
        cat_file(args.target)

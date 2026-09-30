import multiprocessing
import time
import os
import random

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(agent, dept, task, status, color):
    print(f"{color}{Colors.BOLD}[{agent} | {dept}]{Colors.END} {task} -> {status}")

def vance_red_team_worker():
    time.sleep(0.5)
    print_status("VANCE", "Red Team", "Initiating Sandbox Escape Protocol", "ACTIVE", Colors.WARNING)
    time.sleep(1)
    print_status("VANCE", "Red Team", "Fuzzing L2 Cache Boundaries", "INJECTING FAULTS", Colors.WARNING)
    time.sleep(1.5)
    print_status("VANCE", "Red Team", "Fracture Detected at Hexological Node 4096", "ATTEMPTING BREAKOUT", Colors.FAIL)
    time.sleep(1)
    print_status("VANCE", "Red Team", "Breakout Failed. Sandbox Wall Held.", "REBUILDING STRONGER", Colors.GREEN)

def clara_rnd_worker():
    time.sleep(0.7)
    print_status("CLARA", "R&D / Research", "Loading Hieroglyphic & Roman Numeral Cipher", "ACTIVE", Colors.CYAN)
    time.sleep(1.2)
    print_status("CLARA", "R&D / Research", "Factoring Non-Linear Prime Matrix (MMDCCLXXVI x IV)", "COMPUTING", Colors.CYAN)
    time.sleep(1.3)
    print_status("CLARA", "R&D / Research", "Cipher Decoded. Logic Path Stressed to 98%", "SUCCESS", Colors.GREEN)

def maxx_hr_worker():
    time.sleep(0.3)
    print_status("MAXX", "HR / Orchestration", "Auditing Idle Departments", "ACTIVE", Colors.BLUE)
    time.sleep(0.8)
    idle_count = random.randint(30, 42)
    print_status("MAXX", "HR / Orchestration", f"Detected {idle_count} Idle Background Engines", "ROUTING TO DOJO", Colors.BLUE)
    time.sleep(1.4)
    print_status("MAXX", "HR / Orchestration", "All Engines Fully Loaded. Zero Leaks.", "ENFORCED", Colors.GREEN)

if __name__ == "__main__":
    print(f"\n{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}                [XMARS] DOJO PRESSURE CHAMBER ACTIVATED                  {Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}\n")
    
    # Run the Trinity in parallel
    p1 = multiprocessing.Process(target=vance_red_team_worker)
    p2 = multiprocessing.Process(target=clara_rnd_worker)
    p3 = multiprocessing.Process(target=maxx_hr_worker)
    
    p1.start()
    p2.start()
    p3.start()
    
    p1.join()
    p2.join()
    p3.join()
    
    print(f"\n{Colors.BOLD}========================================================================={Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}TRINITY PROTOCOL ENFORCED. ZERO IDLE ENGINES. DOJO IS LOCKED IN.{Colors.END}")
    print(f"{Colors.BOLD}========================================================================={Colors.END}\n")


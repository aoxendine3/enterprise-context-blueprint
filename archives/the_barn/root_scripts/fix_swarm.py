import sys

with open('/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/test_max_swarm_push.py', 'r') as f:
    content = f.read()

content = content.replace('run_max_swarm_push(total_agents=300, max_concurrency=24, adversarial_ratio=0.15)', '''import sys
    agents = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    run_max_swarm_push(total_agents=agents, max_concurrency=concurrency, adversarial_ratio=0.15)''')

with open('/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/test_max_swarm_push.py', 'w') as f:
    f.write(content)

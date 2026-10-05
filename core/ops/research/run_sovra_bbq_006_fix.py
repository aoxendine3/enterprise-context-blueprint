import sys
with open("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/research/run_sovra_bbq_006.py", "r") as f:
    lines = f.read()
lines = lines.replace("{ m/s}", "{{ m/s}}")
lines = lines.replace("{ K}", "{{ K}}")
lines = lines.replace("{ A/m}", "{{ A/m}}")
lines = lines.replace("{SH}", "{{SH}}")
lines = lines.replace("{FM}", "{{FM}}")
with open("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/research/run_sovra_bbq_006.py", "w") as f:
    f.write(lines)

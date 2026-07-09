import os
import json
import subprocess
from typing import Dict, Any, List

# Wrapper for IBM Quantum QAOA optimization
# Requires IBM Quantum API key present in environment variable IBM_QUANTUM_API_KEY

IBM_API_KEY = os.getenv('IBM_QUANTUM_API_KEY')

def _run_qiskit_qaoa(problem_json: str) -> Dict[str, Any]:
    """Run QAOA on the given problem definition using Qiskit.

    The problem_json should encode a quadratic unconstrained binary optimization (QUBO)
    or Ising model representation. This function writes the JSON to a temporary file,
    invokes a Python script that uses Qiskit, and returns the solution dict.
    """
    tmp_path = '/tmp/qaoa_problem.json'
    with open(tmp_path, 'w') as f:
        f.write(problem_json)
    script_path = os.path.join(os.path.dirname(__file__), 'qaoa_runner.py')
    cmd = ['python3', script_path, tmp_path]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, 'IBM_QUANTUM_API_KEY': IBM_API_KEY})
    if result.returncode != 0:
        raise RuntimeError(f'QAOA execution failed: {result.stderr}')
    return json.loads(result.stdout)

def optimize_constraints(constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Given a list of constraint definitions, build a QUBO and solve via QAOA.

    Returns the optimal assignment of boolean variables that satisfy the constraints
    as much as possible.
    """
    qubo = {}
    for c in constraints:
        vars_ = c.get('variables', [])
        weight = c.get('weight', 1)
        for i in range(len(vars_)):
            for j in range(i, len(vars_)):
                key = (vars_[i], vars_[j])
                qubo[key] = qubo.get(key, 0) + weight
    problem = {'type': 'qubo', 'coefficients': qubo}
    problem_json = json.dumps(problem)
    return _run_qiskit_qaoa(problem_json)

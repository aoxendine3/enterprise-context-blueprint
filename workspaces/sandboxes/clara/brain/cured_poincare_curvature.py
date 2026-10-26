import math

def calculate_poincare_curvature(u, v):
    """
    Clara-Verified Poincaré Hyperbolic Metric & Constant Negative Gaussian Curvature (-1.0).
    d_H(u, v) = acosh(1 + 2 * ||u - v||^2 / ((1 - ||u||^2) * (1 - ||v||^2)))
    """
    norm_u_sq = sum(x**2 for x in u)
    norm_v_sq = sum(x**2 for x in v)
    if norm_u_sq >= 1.0 or norm_v_sq >= 1.0:
        raise ValueError("Coordinates must be strictly within unit disk ||x|| < 1.0")
    diff_sq = sum((x - y)**2 for x, y in zip(u, v))
    arg = 1.0 + (2.0 * diff_sq) / ((1.0 - norm_u_sq) * (1.0 - norm_v_sq))
    hyperbolic_dist = math.acosh(arg)
    gaussian_curvature = -1.0 # Invariant for hyperbolic plane
    return hyperbolic_dist, gaussian_curvature

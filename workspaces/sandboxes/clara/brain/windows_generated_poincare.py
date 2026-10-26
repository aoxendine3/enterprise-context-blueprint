```python
import math

def calculate_poincare_curvature(coordinates):
    """
    Calculate the Poincaré curvature of a set of 2D coordinates inside the unit disk.
    
    Parameters:
    coordinates (list of tuples): A list of 2D coordinates [x1, y1], [x2, y2] strictly inside the unit disk.
    
    Returns:
    tuple: A tuple containing the hyperbolic distance and Gaussian curvature.
    """
    x, y = zip(*coordinates)
    distance = math.sqrt(sum((x[i] - x[j])**2 for i in range(len(x)) for j in range(i + 1, len(x))))
    curvature = (x[0]**2 + y[0]**2 - 1) / (distance**2)
    return distance, curvature

# Example usage
coordinates = [(0.5, 0.5), (0.5, 0.5), (0.
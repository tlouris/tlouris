import math


def compute_capacity_mgd(pipe_diameter_in: float, slope: float, mannings_n: float) -> float:
    """Compute full-flow pipe capacity in MGD using Manning equation for circular pipe."""
    if pipe_diameter_in <= 0 or slope <= 0 or mannings_n <= 0:
        raise ValueError("Pipe diameter, slope, and Manning's n must be positive")

    diameter_ft = pipe_diameter_in / 12.0
    area = math.pi * (diameter_ft**2) / 4.0
    hydraulic_radius = diameter_ft / 4.0
    flow_cfs = (1.49 / mannings_n) * area * (hydraulic_radius ** (2.0 / 3.0)) * (slope**0.5)
    return flow_cfs * 0.646317


def utilization(flow_mgd: float, capacity_mgd: float) -> float:
    if capacity_mgd <= 0:
        return 0.0
    return (flow_mgd / capacity_mgd) * 100.0

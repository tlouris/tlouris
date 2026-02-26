from app.services.capacity import compute_capacity_mgd, utilization


def test_capacity_positive():
    val = compute_capacity_mgd(24, 0.001, 0.013)
    assert val > 0


def test_utilization_math():
    assert utilization(5, 10) == 50.0

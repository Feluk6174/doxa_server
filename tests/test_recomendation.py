import pytest

import recomendation
#from matplotlib import pyplot as plt



def test_clustering_2_clusters_2d(users_2d_2clusters):
    clusters = recomendation.cluster(users_2d_2clusters)
    assert clusters[:10] == [clusters[0] for _ in range(10)]
    assert clusters[10:] == [clusters[-1] for _ in range(10)]
    assert clusters[0] != clusters[-1]

def test_clustering_2_clusters_3d(users_3d_2clusters):
    clusters = recomendation.cluster(users_3d_2clusters)
    assert clusters[:10] == [clusters[0] for _ in range(10)]
    assert clusters[10:] == [clusters[-1] for _ in range(10)]
    assert clusters[0] != clusters[-1]

@pytest.mark.parametrize("num_users,dimentions", [(0, 2), (16, 2), (80, 2), (81, 3), (300, 4)])
def test_calc_dimentions(num_users, dimentions):
    assert recomendation.calc_dimentions(num_users) == dimentions

def test_calc_dimentions_negative():
    with pytest.raises(ValueError):
        assert recomendation.calc_dimentions(-1) == 2


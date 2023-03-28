import pytest
import random

random.seed("doxa_tests")
def gen_users_nd_2clusters(n_dimentions):
    size = 15
    users = []
    cluster1_pos = [20 for _ in range(n_dimentions)]
    cluster2_pos = [80 for _ in range(n_dimentions)]

    for _ in range(10):
        users.append([cluster1_pos[i]+random.randint(-size, size) for i in range(n_dimentions)])

    for _ in range(10):
        users.append([cluster2_pos[i]+random.randint(-size, size) for i in range(n_dimentions)])

    return users

@pytest.fixture
def users_2d_2clusters():
    return gen_users_nd_2clusters(2)


@pytest.fixture
def users_3d_2clusters():
    return gen_users_nd_2clusters(3)
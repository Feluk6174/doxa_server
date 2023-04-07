import database
import json
import random

from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.datasets import make_blobs

def calc_dimentions(num_users:int) -> int:
    if num_users < 0:
        raise ValueError("num_users hasto be 0 or more")
    dimentions = int(num_users**0.25)
    if dimentions < 2:
        dimentions = 2
    return dimentions

def num_clusters(db:database.Database):
    return len(db.querry("SELECT id FROM groups;"))

def create_groups(nums:list[int], db:database.Database):
    nums_db = db.querry("SELECT id FROM grups;")
    if not len(nums) == len(nums_db):
        for num in nums:
            if not num in nums_db:
                db.execute(f"INSERT INTO grups(id, pos) VALUES({num}, "+'{"pos": '+str([random.randint(0, 100), random.randint(0, 100)])+'}')


def cluster(users:list[list[int]]) -> list[int]:
    bandwidth = estimate_bandwidth(users, quantile=0.4)
    meanshift = MeanShift(bandwidth=bandwidth)
    meanshift.fit(users)

    return list(meanshift.predict(users))

def normalize_user_positions(users:list[list], dimentions:int):
    if dimentions > len(users[0][2]):
        for _ in range(dimentions-len(users[0][2])):
            for i in range(len(users)):
                users[i][2].append((users[i][1]/dimentions)*100)
    elif dimentions < len(users[0][2]):
        # TODO
        pass
    return users

def calc_clusters(db:database.Database):
    users = db.get_users_with_pos()
    dimentions = calc_dimentions(len(users))

    print(dimentions)
    print(users)

    users = normalize_user_positions(users, dimentions)

    positions = [user[2] for user in users]
    new_group  = cluster(positions)
    
    create_groups(list(set(new_group)))

    print(new_group)

    for i in range(len(users)):
        users[i][1] = new_group[i]

    print(users)

    db.update_users_pos(users)


if __name__ == "__main__":
    db = database.Database()
    #db.create()
    calc_clusters(db)

import database
import json

from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.datasets import make_blobs

def calc_dimentions(db:database.Database):
    users = db.querry("SELECT user_name, grup, pos FROM users;")
    dimentions = int(len(users)**0.25)
    if dimentions < 2:
        dimentions == 2
    return dimentions

def num_clusters(db:database.Database):
    return len(db.querry("SELECT id FROM groups;"))

def calc_clusters(db:database.Database):
    users = db.querry("SELECT user_name, grup, pos FROM users;")
    dimentions = calc_dimentions(db)

    print(dimentions)
    
    users = [[user[0], user[1], json.loads(user[2])["pos"]] for user in users]

    print(users)

    if dimentions > len(users[0][2]):
        for _ in range(dimentions-len(users[0][2])):
            for i in range(len(users)):
                users[i][2].append((users[i][1]/dimentions)*100)
    elif dimentions < len(users[0][2]):
        # TODO
        pass

    poss = [user[2] for user in users]

    bandwidth = estimate_bandwidth(poss, quantile=0.2, n_samples=500)
    meanshift = MeanShift(bandwidth=bandwidth)
    meanshift.fit(poss)

    grup_pred  = meanshift.predict(poss)

    print(grup_pred)

    for i in range(len(users)):
        users[i][1] = grup_pred[i]

    print(users)

    for user in users:
        db.execute(f"UPDATE users SET grup = {user[1]} WHERE user_name = '{user[0]}';")


if __name__ == "__main__":
    db = database.Database()
    #db.create()
    calc_clusters(db)

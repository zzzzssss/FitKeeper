# Cteate a 'databases' folder, put aws_identity.txt and dynamodb.py inside
import sys, time
sys.path.append('databases/')
from dynamodb import *
from db_funcs import *
import numpy as np
from sklearn.cluster import KMeans


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)
            
# db = [(),(),...]
def kmeans(db):
    """
    Input:
        db: A list of tuples, each tuple corresponds 
            to one user.
            This should be the output of function "read_db_to_ml()"
    Return:
        group: 
            Used to lookup the cluster that each user is in.
            Dictionary format.
            key: Each user's uid
            value: cluster's index
        get_group_member: 
            Used to find components of each cluster.
            Dictionary format.
            key: Cluster index, STRING TYPE
            value: A list containing all members of this cluster
    """
    group = {}
    get_group_member = {}

    data_list = []
    id = []
    for data in db:
        id.append(data[0])
        data_list.append(data[1:])

    df = np.array(data_list)
    k = 10

    for i in range(0, k):
        get_group_member[i] = []
    clf = KMeans(n_clusters=k).fit(df)
    labels = clf.labels_
    for i in range(0, len(labels)):
        group[id[i]] = labels[i]
        get_group_member[labels[i]].append(id[i])
    
    # Encode "numpy" integers to serializable ones
    group = json.loads(json.dumps(group, cls=MyEncoder))
    get_group_member = json.loads(json.dumps(get_group_member, cls=MyEncoder))
    
    return group, get_group_member 


def main_func():
    """
    Main Function. 
        1. Read data from Profile DB
        2. Run K-means
        3. Store Results in DynamoDB
    """
    db = connect_db()   # Connect to Profile DB

    all_data = read_db_to_ml(db)
    g, ggm = kmeans(all_data)

    write_to_kmeans_users(g)
    write_to_kmeans_cluster(ggm)

    return None


if __name__ == '__main__':
    print "K-Means worker starts."
    while True:
        try:
            main_func()
            time.sleep(60)
        except KeyboardInterrupt:
            print "Quitting...\n"
            break
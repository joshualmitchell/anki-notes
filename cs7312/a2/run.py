import numpy as np
import pandas as pd
import sys

def distance(a, b, ax=1):
    return np.linalg.norm(a - b, axis=ax)
            
def get_new_labels_iteration(X, centroids):
    new_labels = [np.argmin(distance(X[i], centroids)) for i in range(len(X))]
    return new_labels

def kmeans(k, file_name):
    data = pd.read_csv(file_name, header = None, sep='\t')
    print("k: ", k, "   filename: ", file_name)
    x1 = data[0].values
    x2 = data[1].values
    
    # centroid_x = np.random.randint(np.mean(x1) - np.std(x1), np.mean(x1) + np.std(x1), size=k)
    # centroid_y = np.random.randint(np.mean(x2) - np.std(x2), np.mean(x2) + np.std(x2), size=k)
    centroid_x = np.array([np.max(x1) / (i + 1) for i in range(k)])
    centroid_y = np.array([np.max(x2) / (i + 1) for i in range(k)])
    # centroid_x = np.random.randint(0, np.max(x1), size=k)
    # centroid_y = np.random.randint(0, np.max(x2), size=k)
    
    X = np.array(list(zip(x1, x2)))
    centroids = np.array(list(zip(centroid_x, centroid_y)))
    
    temp_centroids = np.zeros(centroids.shape)
    cluster_labels = np.zeros(len(X))

    error = distance(centroids, temp_centroids, None)

    while error != 0:
        cluster_labels = get_new_labels_iteration(X, centroids)
        temp_centroids = centroids.copy()
        for i in range(k):
            points = [X[j] for j in range(len(X)) if cluster_labels[j] == i]
            centroids[i] = np.mean(points, axis=0)
            if np.isnan(centroids[i]).any(): # in case we end up having a centroid with no points in it
                centroids[i][0] = np.random.randint(0, np.max(x1))
                centroids[i][1] = np.random.randint(0, np.max(x2))
        error = distance(centroids, temp_centroids, None)
    colors = ['r', 'g', 'b', 'y', 'c', 'm']
    Out = np.array(list(zip(X[:, 0], X[:, 1], cluster_labels)))
    df = pd.DataFrame(Out)
    return df

if __name__ == "__main__":
    print("--------------------------------------")
    print("Arguments: ", sys.argv)
    k = int(sys.argv[1])
    file_name = str(sys.argv[2])
    df = kmeans(k, file_name)
    df.to_csv('output.txt', header=None, index=None, sep=' ', mode='w')
import numpy as np
import kdtree
from sklearn.cluster import DBSCAN

class Bot(object):

    def __init__(self, x, y, id):
        self.coords = (x, y)
        self.id = id
        self.pos = None
        self.neg = None
        self.id = id
        self.angle = None

    def __getitem__(self, i):
        return self.coords[i]

    def __len__(self):
        return len(self.coords)

    def __repr__(self):
        return 'Item(x:{}, y:{}, pos:{}, neg:{}, id:{}, angle:{})'.format(self.coords[0], self.coords[1], self.pos, self.neg, self.id, self.angle)

class Clusterer():
    def __init__(self, eps, minpts):
        self.eps = eps
        self.minpts = minpts
    
    def run(self, data):
        x, y = np.where(data != 255)
        points = np.column_stack((x, y))
        clusters = []
        try:
            clustering = DBSCAN(
            eps=self.eps,
            min_samples=self.minpts,
            algorithm='kd_tree',
            ).fit(points)

            # list of every cluster, including noise (assigned to -1).
            found_clusters = set(clustering.labels_)

            # remove noise
            found_clusters.remove(-1)

            # get each label class in it's own cluster collection
            for i, each in enumerate(found_clusters):
                points_with_class = np.column_stack(
                    (points, clustering.labels_))

                detected_pixel_indexes = np.where(
                    points_with_class[:, 2] == each)

                detected_pixels = points_with_class[detected_pixel_indexes]

                clusters.append(detected_pixels[:, 0:2])

            return clusters

        except Exception as e: 
            # we allow this to fail gracefully if no detections are found
            print('Error:{}'.format(e))
            return clusters

class KD_Tree():
    def __init__(self):
        self.tree = kdtree.create(dimensions=2)
        self.nextID = 0

    def asList(self):
        return list(self.tree.inorder())

    def addNode(self, x, y):
        # make a bot with new data
        bot = Bot(x, y, self.nextID)

        # add to tree
        self.tree.add(bot)

        # increment nextID counter
        self.nextID +=1

    def updateNode(self, x, y, neighbor):
        # save the neighbor's id
        id = neighbor[0].data.id

        # remove old match
        self.tree = self.tree.remove(neighbor[0].data)

        # make a bot with new coordinates and old ID
        bot = Bot(x, y, id)

        # insert bot to tree
        self.tree.add(bot)

    def NN(self, x, y):
        return self.tree.search_nn((x,y))
import numpy as np
import math

def getCentroids(clusters):
    centroids = []
    for cluster in clusters:
        meanY = int(np.mean(cluster[:,0]))
        meanX = int(np.mean(cluster[:,1]))
        centroids.append([meanY, meanX])
    return centroids

def getAngleFromTwoCentroids(c1,c2):
    angle = np.arctan2((c2[0] - c1[0]), (c2[1]-c1[1]))
    angle = math.degrees(angle)
    return angle

def changeAngleRef(angle):

    if angle == 0:
        angle = 270

    elif angle == -90:
        angle = 0

    elif angle >= 179 or angle <= -179:
        angle = 90
            
    elif angle == 90:
        angle = 180
            
    ###################

    # first q
    # if its 0 to -90, multiply by -1 then add 270
    elif angle < 0 and angle > -90:
        angle *= -1
        angle += 270

    # second q
    # if it's -90 to -180, multiply by -1 and subtract 90
    elif angle < -90 and angle > -180:
        angle *= -1
        angle -= 90

    # third and 4th q
    # subtract from 270
    elif angle > 0 and angle < 180:
        angle = 270 - angle

    return angle
# external dependencies
import csv
import numpy as np
import cv2
from datetime import datetime
from pytz import timezone

# internal dependencies
from helpers import *
from idTrack import KD_Tree, Clusterer

filename = './data/4botcircle100.csv'

tz = timezone('EST')
logname = datetime.now(tz).strftime("%Y-%m-%d-%H-%M-%S-%f") + '_eventlog.csv'

def main():

    # the duration of the sliding window to accumulate events
    accumulation_time = 100000

    # width of a bot in tree distance
    bot_width = 100
    
    frame_count = 0

    # event data from input csv
    data = parseCSV(filename)

    # start time is the reported time of our first event
    start_time = int(data[0][3])

    # end time is the length of our current sliding window
    end_time = start_time + accumulation_time

    # create numpy array of resolution size, 3 dimensions, and fill it with 255 (white pixel color)
    frame = np.full((640, 480, 3), 255)

    # KD tree to store bot info over time
    tree = KD_Tree()

    # for each event
    for line in data:

        # parse out the info for each event
        x = int(line[0])
        y = int(line[1])
        polarity = int(line[2])
        time = int(line[3])

        # if current time is within our accumulation time sliding window
        if time <= end_time:

            # add the event to a pos or neg numpy array
            frame[x][y][polarity] = 0
            
            # add the event to the full set array
            frame[x][y][2] = 0

        else:
            # accumulated frames as int and named appropriately
            pos = frame[:, :, 0].astype('uint8')
            neg = frame[:, :, 1].astype('uint8')
            full = frame[:, :, 2].astype('uint8')

            # use dbscan to create list of clusters for each data set
            pos_clusters = Clusterer(6,50).run(pos)
            neg_clusters = Clusterer(6,50).run(neg)
            full_clusters = Clusterer(15,170).run(full)

            # find centroids of each cluster
            pos_centroids = getCentroids(pos_clusters)
            neg_centroids = getCentroids(neg_clusters)
            full_centroids = getCentroids(full_clusters)

            # perform tracking on each centroid
            for centroid in full_centroids:
                bot_x = centroid[1]
                bot_y = centroid[0]

                # initialization step
                if not tree.tree:
                    tree.addNode(bot_x, bot_y)
                
                else:
                    # find distance to nearest neighbor
                    neighbor = tree.NN(bot_x, bot_y)
                    distanceFromNeighbor = neighbor[1]

                    # if it's too great, new bot
                    if distanceFromNeighbor > bot_width:
                        tree.addNode(bot_x, bot_y)
                    
                    # if a prev bot was at this location
                    else:
                        tree.updateNode(bot_x, bot_y, neighbor)
            
            # examine pos clusters to find bot centroid
            for pos in pos_centroids:

                # find the nearest neighbor of positive cluster, 
                # this will be the bot centroid
                neighbor = tree.NN(pos[1], pos[0])

                try:
                    neighbor[0].data.pos = (pos[1], pos[0])
                except:
                    print("No pos neighbor found")

            # examine neg clusters to find bot centroid
            for neg in neg_centroids:

                # find the nearest neighbor of neg cluster
                # this will be the bot centroid
                neighbor = tree.NN(neg[1], neg[0])

                try:
                    neighbor[0].data.neg = (neg[1], neg[0])
                except:
                    print("No neg neighbor found")
            
            tree_list = tree.asList()

            # Form angles and assign
            for bot in tree_list:

                # get x,y of bot
                x = bot.data.coords[0]
                y = bot.data.coords[1]

                # find neighbor (which is actually the bot itself represented in the tree)
                neighbor = tree.NN(x, y)

                # get pos,neg coord
                pos = neighbor[0].data.pos
                neg = neighbor[0].data.neg

                # angle from pos, neg
                try:
                    angle = getAngleFromTwoCentroids(pos,neg)
                    angle = changeAngleRef(angle)

                    # store angle
                    neighbor[0].data.angle = round(angle,1)
                except:
                    pass
            
            # write bot data to output csv
            csvWrite(tree_list, frame_count)
            
            # create an image from the full data set
            grayImg = cv2.cvtColor(full, cv2.COLOR_GRAY2BGR)

            # draw info on image (centroids and labels)
            drawAnnotations(grayImg, tree_list)

            # display image and wait 25ms
            cv2.imshow('', grayImg)
            cv2.waitKey(25)

            # put this event into a new frame
            frame = np.full((640, 480, 3), 255)
            frame[x][y][polarity] = 0

            # advance frame count
            frame_count += 1

            # slide the accumulation time up
            start_time = time
            end_time = start_time + accumulation_time

def parseCSV(filename):
    data = []
    # read csv into data list
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            data.append(row)
    return data

# each frame, draw labels of bot info on img from tree 
def drawAnnotations(img, tree_list):
    for bot in tree_list:
        # x,y coordinates of bot
        b_x = int(bot.data.coords[0])
        b_y = int(bot.data.coords[1])

        # id of bot
        b_id = bot.data.id

        # angle of bot
        b_angle = bot.data.angle

        # string formatting for label
        coords = '(' + str(b_x) + ' , ' + str(b_y) + ')'
        angle = str(b_angle) + ' deg'
        
        # place our strings on the image at some curated locations
        cv2.putText(img, str(b_id), (b_x - 10, b_y - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
        cv2.putText(img, coords, (b_x - 10, b_y - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
        cv2.putText(img, angle, (b_x - 10, b_y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)

        # draw a nice box around each bot's label
        cv2.rectangle(img, 
            (b_x - 15, b_y - 20), 
            (b_x + 90, b_y - 90),
            2)
        
        # draw a circle at the bot's centroid
        cv2.circle(img, (b_x, b_y), 4, (0,0,255), -1)

def csvWrite(bots, frame_num):
    # the log files are created in the format of
    # [time, frame number, x location, y location, angle, robot id]
    # each robot in a frame will get it's own line
    with open(logname, mode='a') as event_data:
        event_writer = csv.writer(event_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # scene unique data
        now = datetime.now(tz)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")
        date, time = timestamp.split(' ')
        h,m,sec = time.split(':')
        s,us = sec.split('.')

        for bot in bots:
            # bot unique data, rounded to two significant figures where applicable
            x = round(bot.data[0],2)
            y = round(bot.data[1],2)
            id_num = bot.data.id
            angle = bot.data.angle
            
            # combine all time info into one seconds variable
            time_in_s = str(int(h)*3600 + int(m)*60 + int(s) + float(us)*(10**-6))
            
            # write to file
            event_writer.writerow([time_in_s, frame_num, x, y, angle, id_num])

if __name__ == '__main__':
    main()
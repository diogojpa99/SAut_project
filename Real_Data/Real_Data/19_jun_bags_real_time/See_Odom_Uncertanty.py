""" *********************************** Libraries ************************************************* """

import numpy as np
import matplotlib.pyplot as plt
from math import pi, radians, degrees, sin, cos


import plots as pl
import Real_Map as map
import Paricle_Filter as pf
import Get_Data_60_measures as data


""" ************************************* Global Variables ****************************************  """

''' Particles '''

# Number of particles
original_M = M = 1000

# Flag that defines the number of particles
# resize_flag = 0 : Don't do nothing
# resize_flag = 1 : Increase number of particles
# resize_flag = 2 : Decrease number of particles
resize_flag = 0

# Particles
particles = np.empty([M, 3])

''' Weights '''

w = np.empty([M,1])
w.fill(1.)

''' Robot '''

# Robot Localization
robot_loc = np.empty([3,1])

''' Actions '''

# Actions
# action[0] : Distance traveled
# action[1] : Rotation
actions = np.empty([2,1])
actions[0] = 0
actions[1] = 1

# Last Iteration
last_iteration = actions.shape[0]

''' Optimize the algorithm '''

likelihood_avg = 1 #Likelihoods Average
n_eff = M # n_eff 
resampling_flag = 1 # Resampling Flag

''' Output '''

# Errors
errors = np.empty([last_iteration,3])
errors.fill(1.)


"""  ************************************ Functions  ******************************************** """

# init_robot_pos():
# Initialize the robot position
# loc[0] : x variable
# loc[1] : y variable
# loc[2] : Orientation

def init_robot_pos(loc):

    loc[0] = 9.5
    loc[1] = 0.85
    loc[2] = radians(175)

    return loc


""" *********************************** main() *********************************************** """

# Create particles
particles = map.create_particles(M)
for i in range (M):
    particles[i] = map.validate_loc(particles[i])

# Plotting
# Activationg interactive mode
plt.ion()

robot_loc = init_robot_pos(robot_loc)

k = 0
while(1):

    # *********************** Robot simulation ******************************** #
    print("-----------------------------------------------------------------------------------")
    print("\t\t\tIteration nº:",k+1)

    real_x, real_y, real_theta, actions[0], actions[1], measures = data.get_data()
    measures = np.array(measures)
    if len(measures) != 0:
        robot_measures = measures.reshape([measures.shape[1],1])
        robot_measures[np.isnan(robot_measures)] = 0

    if (k < 11 and actions[0] == 0 and actions[1] == 0):
        robot_loc[0] = real_x
        robot_loc[1] = real_y
        robot_loc[2] = real_theta


    # Update localization of the robot
    robot_loc = pf.odometry_model(robot_loc, actions[0], radians(actions[1]), 0)
    robot_loc = map.validate_loc(robot_loc)

    #artificial_measures = pf.laser_model(robot_loc,map.n_walls,robot_loc,map)

    if (actions[0] == 0 and actions[1] == 0): 
        print('ROBOT DID NOT MOVE')
    
    # Plot Map
    for i in range(31):
        plt.plot((map.map[i][0][0],map.map[i][1][0]),(map.map[i][0][1],map.map[i,1,1]), c = 'black')
    
    # Plot robot
    radius = -119
    if len(measures) != 0:
        for i in range (robot_measures.shape[0]):
            plt.scatter(robot_loc[0] + robot_measures[i]*cos(robot_loc[2] + radians(radius)), robot_measures[i]*sin(robot_loc[2] + radians(radius)) + robot_loc[1], s = 4,  c = '#e377c2')   
            radius += 4

    plt.scatter(robot_loc[0], robot_loc[1], marker = (6, 0, robot_loc[2]*(180/pi)), c = '#d62728' , s=80, label = "Real position", edgecolors='black')
    plt.plot((robot_loc[0],(1/100)*cos(robot_loc[2])+robot_loc[0]),(robot_loc[1],(1/100)*sin(robot_loc[2])+robot_loc[1]), c = '#17becf')
    plt.pause(0.01)
    plt.show()
    plt.clf()

    print('Real Loc:',"\t", real_x,"\t", real_y,"\t", real_theta)
    print('Robot Loc:',"\t", robot_loc[0][0],"\t", robot_loc[1][0],"\t", robot_loc[2][0]*(180/pi))
    
    # ************************** Algorithm  ********************************** #

    '''

    print("Nº of particles:", M)
    if (actions[k][0] == 0 and actions[k][1] == 0):
        print('ROBOT DID NOT MOVE')
    else:

        # PREDICT
        particles = pf.predict(particles, actions[k], M)
        for i in range (M):
            particles[i] = map.validate_loc(particles[i])
        
        # UPDATE
        w, likelihood_avg, resize_flag = pf.update(w, robot_measures, particles, resampling_flag, likelihood_avg, M, robot_loc, map)
        
        # n_eff
        n_eff_inverse = 0

        for m in range (M):
            n_eff_inverse = n_eff_inverse + pow(w[m],2)
        
        n_eff = 1/n_eff_inverse
        print("[Neff] -> ", n_eff)
        if ( n_eff < M*0.27 ):
            resampling_flag = 1
        else:
            resampling_flag = 0
            resize_flag = 2
        
        # RESAMPLING
        if (resampling_flag == 1):
            particles = pf.low_variance_resample(w, M , particles)
        else:
            print('NO RESAMPLE')
    
    # Resizing the number of particles
    if resize_flag == 1:

        # High probability of kidnapping
        more_particles = map.create_particles( int(M*1.2))
        more_particles[0:M] = particles
        particles = more_particles
        M = int(M*1.2)
        
        for i in range (int(M*0.9)):
            particles[i] = map.reposition_particle(particles[i], i )
            particles[i] = map.validate_loc(particles[i])

    
    elif resize_flag == 2:

        if ( M > int(original_M*0.3)):
            M = int(M*0.8)
            particles = particles[0:M]
        
    # ************************** Output ********************************** #

    # Centroid of the cluster of particles
    pred_angle = np.average(particles[:,2])
    robot_angle = robot_loc[2][0]

    if pred_angle > pi:
        pred_angle -= 2*pi
    elif pred_angle < -pi:
        pred_angle += 2*pi

    if robot_angle > pi:
        robot_angle = robot_angle - 2*pi
    elif robot_angle < -pi:
        robot_angle += 2*pi

    errors[k][0] = abs(np.average(particles[:,0])-robot_loc[0][0])
    errors[k][1] = abs(np.average(particles[:,1])-robot_loc[1][0])   
    errors[k][2] = abs(pred_angle - robot_angle) 

    if ( errors[k][2] > (5/3)*pi):
         errors[k][2] = abs(2*pi - errors[k][2])
        
    print('Real Loc:',"\t", robot_loc[0][0],"\t", robot_loc[1][0],"\t", robot_angle*(180/pi))
    print("Pred Loc:", "\t", np.average(particles[:,0]),"\t", np.average(particles[:,1]),"\t", pred_angle*(180/pi))
    print("ERROR:  ","\t",errors[k][0],"\t", errors[k][1],"\t", degrees(errors[k][2]))

    # Plotting
    pl.plot_simulation('Particle Filter Simulation',robot_loc, particles, map.n_walls, map.map, M)
    plt.clf()

    if ( ((errors[k][0] < 0.005) and (errors[k][1] < 0.005) and (errors[k][2] < 0.005)) or k == last_iteration-1):
        break

    '''
    k +=1

# Plotting Statistics
pl.plot_erros(errors)
#!/usr/bin/env python3
import math
import rospy
import numpy as np
from robot_vision_lectures.msg import XYZarray
from robot_vision_lectures.msg import SphereParams

# Define global variables, these are used to build A and B matricies:
b_data = []
a_data = []
received = False

# Callback function to get ball data from publisher:
def get_ball_data(data):
	
	# Access global variables:
	global received
	global b_data
	global a_data
	
	# Redefine lists as empty for each new dataset:
	b_data = []
	a_data = []
	
	# Build data foor A and B:
	for point in data.points:
		
		b_data.append((point.x)**2 + (point.y)**2 + (point.z)**2)
		
		a_data.append([2*point.x, 2*point.y, 2*point.z, 1])
	
	received = True
	

# Function to filter the data:
def filter_data(data, fil_out, fil_gain):
	
	# Initialise values before calculations:
	fil_in = data
	
	# Filter equation:
	fil_out = (fil_gain*fil_in) + (1 - fil_gain)*fil_out
	
	return fil_out


if __name__ == '__main__':
	
	# Initialize the node:
	rospy.init_node('sphere_fit', anonymous = True)
	
	# Add a subscriber for the XYZ data:
	rospy.Subscriber('xyz_cropped_ball', XYZarray, get_ball_data)
	
	# Define publisher:
	sphere_pub = rospy.Publisher('/sphere_params', SphereParams, queue_size = 1)
	
	# This was a seperate pub that I used to compare the initial and filtered data in rqt_plot:
	# filter_pub = rospy.Publisher('/filtered_params', SphereParams, queue_size = 1)
	
	# Set loop frequency:
	rate = rospy.Rate(10)
	
	# Set initial variables for filter equation:
	x_fil_out = -0.015
	y_fil_out = -0.019
	z_fil_out = 0.48
	r_fil_out = 0.06
	
	# Gains are easily adjustable:
	point_gain = 0.0005
	radius_gain = 0.005
	
	while not rospy.is_shutdown():
	
		if received:
			
			# Define the A matrix:
			A = np.array(a_data)
			
			# Define the B matrix:
			B = np.array([b_data]).T
			
			# Check validity of data to avoid errors:
			if A.shape[0] == B.shape[0] and len(A.shape) == 2 and len(B.shape) == 2:
			
				# Calculate P:
				P = np.linalg.lstsq(A, B, rcond=None)[0]
			
				# Get sphere params from P:
				xc = P[0]
				yc = P[1]
				zc = P[2]
				r = math.sqrt(P[3] + xc**2 + yc**2 + zc**2)
				
				# Get filtered data:
				Fxc = filter_data(xc, x_fil_out, point_gain)
				x_fil_out = Fxc
				Fyc = filter_data(yc, y_fil_out, point_gain)
				y_fil_out = Fyc
				Fzc = filter_data(zc, z_fil_out, point_gain)
				z_fil_out = Fzc
				Fr = filter_data(r, r_fil_out, radius_gain)
				r_fil_out = Fr
				
				# This was for the seperate filtered data publisher
				# I have kept it commented here for ease of access later in case I need to access both datasets
				
				#filtered_data = SphereParams()
				#filtered_data.xc = Fxc
				#filtered_data.yc = Fyc
				#filtered_data.zc = Fzc
				#filtered_data.radius = Fr
				#filter_pub.publish(filtered_data)
				
				# Declare variable for publisher:
				sphere_data = SphereParams()
				
				# Add sphere params to publisher:
				sphere_data.xc = Fxc
				sphere_data.yc = Fyc
				sphere_data.zc = Fzc
				sphere_data.radius = Fr
				
				# Publish messge:
				sphere_pub.publish(sphere_data)

############ PHYS 777: MACHINE LEARNING FOR MANY-BODY PHYSICS, TUTORIAL 3 ############
### Dataset and code by Lauren Hayward Sierens and Juan Carrasquilla
###
######################################################################################

import numpy as np
import tensorflow as tf

### Data parameters: ###
num_labels  = 2     # Number of labels (T=0 and T=infinity here)
num_sublattices = 2 # Number of sublattices for the gauge theory lattice

### Hyperparameters: ###
patch_size  = 2     # Size of the filters
num_filters = 64    # Number of output channels in the convolutional layer
nH = 64             # Number of neurons in the fully-connected layer
dropout_prob = 0.5  # Probability of keeping neurons in the dropout layer

############################################################################
########################### READ IN THE DATA SET ###########################
############################################################################

### Read in the training data: ###
x_train_orig = np.loadtxt( 'x_train.txt', dtype='uint8' )
y_train      = np.loadtxt( 'y_train.txt', dtype='uint8' )
N_train      = x_train_orig.shape[0]
N_spins      = x_train_orig.shape[1]
L            = int( np.sqrt(N_spins/2) )

### Read in the test data: ###
x_test_orig = np.loadtxt( 'x_test.txt', dtype='uint8' )
y_test      = np.loadtxt( 'y_test.txt', dtype='uint8' )
N_test      = x_test_orig.shape[0]

#N_train=2
#L = 4
#xxx = np.zeros((N_train,2*L*L))
#for i in range(N_train):
#    xxx[i] = np.arange(2*L*L)

### Enlarge the datapoints based on the patch size (because of periodic boundary conditions): ###
L_enlarged = L+patch_size-1
n0 = 2*(L_enlarged)**2
def enlarge_data(N_samples,data_orig):
    data_enlarged = np.zeros((N_samples,n0))

    for iy in range(L):
        data_enlarged[:,2*iy*L_enlarged:(2*iy*L_enlarged + 2*L)] = data_orig[:,2*iy*L:2*(iy+1)*L]
        data_enlarged[:,(2*iy*L_enlarged + 2*L):2*(iy+1)*L_enlarged] = data_orig[:,2*iy*L:(2*iy*L+2*(patch_size-1))]
    data_enlarged[:,2*L*L_enlarged:] = data_enlarged[:,0:2*L_enlarged*(patch_size-1)]
    return data_enlarged

x_train = enlarge_data(N_train, x_train_orig)
x_test  = enlarge_data(N_test,  x_test_orig)

############################################################################
##################### DEFINE THE NETWORK ARCHITECTURE ######################
############################################################################

x = tf.placeholder(tf.float32, shape=[None, n0]) # Placeholder for the spin configurations
x_reshaped = tf.reshape( x, [-1,L_enlarged,L_enlarged,num_sublattices] )
y = tf.placeholder(tf.int32, shape=[None]) # Labels

### Layer 1 (Convolutional layer): ###
W1 = tf.Variable( tf.truncated_normal([patch_size, patch_size, num_sublattices, num_filters], mean=0.0, stddev=0.01, dtype=tf.float32) )
b1 = tf.Variable( tf.constant(0.1,shape=[num_filters]) )

# Apply the convolution (note that 'VALID' means no padding):
z1 = tf.nn.conv2d(x_reshaped, W1, strides=[1, 1, 1, 1], padding='VALID') + b1
a1 = tf.nn.relu( z1 )
a1_flattened = tf.reshape( a1, [-1,L*L*num_filters])

### Layer 2 (Fully-connected layer): ###
W2 = tf.Variable( tf.truncated_normal([L*L*num_filters,nH], mean=0.0, stddev=0.01, dtype=tf.float32) )
b2 = tf.Variable( tf.constant(0.1,shape=[nH]) )
z2 = tf.matmul(a1_flattened, W2) + b2
a2 = tf.nn.relu( z2 )

# Dropout: To reduce overfitting, we apply dropout to the neurons a2 (before the final output layer).
# We create a placeholder for the probability that a neuron's output is kept during dropout, which
# allows us to turn dropout on during training, and turn it off during testing. TensorFlow's
# tf.nn.dropout op automatically handles scaling neuron outputs in addition to masking them, so
# dropout works without any additional scaling.
keep_prob = tf.placeholder("float")
a2_drop = tf.nn.dropout(a2, keep_prob)

### Layer 3 (Fully-connected layer): ###
W3 = tf.Variable( tf.truncated_normal([nH,num_labels], mean=0.0, stddev=0.01, dtype=tf.float32) )
b3 = tf.Variable( tf.constant(0.1,shape=[num_labels]) )
z3 = tf.matmul(a2_drop, W3) + b3
a3 = tf.nn.softmax( z3 )

### Network output: ###
aL = a3

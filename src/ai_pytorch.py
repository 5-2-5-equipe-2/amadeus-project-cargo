import math
import random
from collections import namedtuple

from collections import namedtuple, deque

import numpy as np
import torch
import torch.optim as optim
import torch.nn.functional as F
import torchvision.transforms as T
from itertools import count

from PIL import Image
from torch import nn
from torchvision.transforms import InterpolationMode

import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
PACKAGE_DIM = 3
PACKAGE_INPUT_NUM = 5
INPUT_IMAGE_SIZE = 500

Transition = namedtuple('Transition',
                        ('state', 'action', 'next_state', 'reward'))


class ReplayMemory(object):

    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Save a transition"""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


# Create Ai Neural Network that takes a
# (2d image of the container + the dimensions of 10 packages) and outputs the best position and rotation for a package
class Net(torch.nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.input_size = (1, INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE)
        # the output size of the dense layers is
        # (position_x,position_y, rotation, index) where index a one-hot encoded as a vector
        self.output_size = (2 + 1 + PACKAGE_INPUT_NUM)
        # the conv layer model consists of 3 layers of convolutional neural networks
        self.conv_layers = torch.nn.Sequential(
            torch.nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            torch.nn.ReLU(),
            torch.nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            torch.nn.ReLU(),
            torch.nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            torch.nn.ReLU(),
        )

        # Number of Linear input connections depends on output of conv2d layers
        # and therefore the input image size, so compute it.
        def conv2d_size_out(size, kernel_size=3, stride=1):
            return (size - (kernel_size - 1) - 1) // stride + 1

        convw = conv2d_size_out(conv2d_size_out(conv2d_size_out(INPUT_IMAGE_SIZE)))
        convh = conv2d_size_out(conv2d_size_out(conv2d_size_out(INPUT_IMAGE_SIZE)))
        linear_input_size = convw * convh * 128 + PACKAGE_INPUT_NUM * PACKAGE_DIM
        # the dense layer model is composed of 4 fully connected layers with relu activation functions
        # and a linear output layer.
        # The dimensions data of the packages is concatenated to the output of the last convolutional layer.
        # The output of the dense layer is the position and rotation of the package
        # as well as the selected package index
        self.dense_layers = torch.nn.Sequential(
            torch.nn.Linear(linear_input_size, 1024),
            torch.nn.ReLU(),
            torch.nn.Linear(1024, 512),
            torch.nn.ReLU(),
            torch.nn.Linear(512, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, self.output_size),
        )

    def forward(self, image, list_of_package_dimensions):
        # the input image is passed through the convolutional layers
        x = self.conv_layers(image)
        # the output of the convolutional layers is flattened
        x = x.view(x.size(0), -1)
        # the package dimensions are concatenated to the output of the convolutional layers
        x = torch.cat((x, list_of_package_dimensions), 1)
        # the output of the convolutional layers is passed through the dense layers
        x = self.dense_layers(x)
        return x


BATCH_SIZE = 128
GAMMA = 0.999
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 2000
TARGET_UPDATE = 1e5
BURN_IN = 1000
LEARN_EVERY = 1
LEARNING_RATE = 1e-4
SYNC_TARGET_EVERY = 1000

# the policy network is the network that is trained
policy_net = Net().to(device)
# the target network is the network that is used to calculate the target value
target_net = Net().to(device)
target_net.load_state_dict(policy_net.state_dict())
target_net.eval()

optimizer = optim.RMSprop(policy_net.parameters(), lr=LEARNING_RATE)
memory = ReplayMemory(10000)

steps_done = 0


def select_action(state):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1
    if sample > eps_threshold:
        with torch.no_grad():
            # t.max(1) will return largest column value of each row.
            # second column on max result is index of where max element was
            # found, so we pick action with the larger expected reward.
            return policy_net(state).max(1)[1].view(1, 1)
    else:
        return torch.tensor([[random.randrange(n_actions)]], device=device, dtype=torch.long)


episode_durations = []


def optimize_model():
    if len(memory) < BATCH_SIZE:
        return
    transitions = memory.sample(BATCH_SIZE)
    # Transpose the batch (see https://stackoverflow.com/a/19343/3343043 for
    # detailed explanation). This converts batch-array of Transitions
    # to Transition of batch-arrays.
    batch = Transition(*zip(*transitions))

    # Compute a mask of non-final states and concatenate the batch elements
    # (a final state would've been the one after which simulation ended)
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                            batch.next_state)), device=device, dtype=torch.bool)
    non_final_next_states = torch.cat([s for s in batch.next_state
                                       if s is not None])
    state_batch = torch.cat(batch.state)
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat(batch.reward)

    # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
    # columns of actions taken. These are the actions which would've been taken
    # for each batch state according to policy_net
    state_action_values = policy_net(state_batch).gather(1, action_batch)

    # Compute V(s_{t+1}) for all next states.
    # Expected values of actions for non_final_next_states are computed based
    # on the "older" target_net; selecting their best reward with max(1)[0].
    # This is merged based on the mask, such that we'll have either the expected
    # state value or 0 in case the state was final.
    next_state_values = torch.zeros(BATCH_SIZE, device=device)
    next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0].detach()
    # Compute the expected Q values
    expected_state_action_values = (next_state_values * GAMMA) + reward_batch

    # Compute Huber loss
    criterion = nn.SmoothL1Loss()
    loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    for param in policy_net.parameters():
        param.grad.data.clamp_(-1, 1)
    optimizer.step()

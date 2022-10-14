import random
import time
from enum import Enum
from itertools import combinations, product

import numpy as np
from matplotlib import pyplot as plt

import numpy
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class Shipment:
    """Rectangle Shipment class."""

    def __init__(self, weight: float, height, width, length, awb):
        self.weight = weight
        self.awb = awb
        self.volume = height * width * length

    def __str__(self):
        return f'Shipment( {self.weight}, {self.volume}, {self.awb})'


class Compartment:
    def __init__(self, compartment_id, ):
        pass


# class

# wrapper class for a training instance
class TrainingInstance:
    # TODO: finish this class
    def __init__(self, container_dimensions: numpy.array, package_dimensions_range: numpy.array,
                 package_weight_range: numpy.array, package_count_range: numpy.array,
                 target_center_of_gravity: numpy.array):
        self.container_dimensions = container_dimensions
        self.package_dimensions_range = package_dimensions_range
        self.package_weight_range = package_weight_range
        self.package_count_range = package_count_range
        self.container = Container(
            self.container_dimensions, numpy.array([0, 0, 0]))
        self.target_center_of_gravity = target_center_of_gravity
        self.fitness = 0

    def __str__(self):
        return f'TrainingInstance({self.container}, {self.fitness})'

    def update_fitness(self):
        """
        Calculates the fitness of the training instance
        The fitness is the volume of the container to the highest package minus the volumes of the packages
        divided by the distance of the center of gravity to the target center of gravity
        :return:
        """
        occupied_volume = self.container.get_volume(
            self.container.highest_package.position[2] + self.container.highest_package.volume[2])
        package_volume = self.container.total_package_volume
        distance = numpy.linalg.norm(
            self.container.center_of_gravity - self.target_center_of_gravity)
        self.fitness = (occupied_volume - package_volume) / distance


if __name__ == '__main__':
    # time the execution
    start_time = time.time()
    container1 = Container(numpy.array(
        [100, 100, 100]), numpy.array([0, 0, 0]))
    # add a 100 random packages of nearly every type to the container
    for i in range(200):
        dimensions = numpy.array(
            [random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)])
        package = Shipment(random.randint(
            1, 2), numpy.array(dimensions), f'package {i}')
        container1.add_package(package, numpy.array([random.randint(0, 100 - 10), random.randint(0, 100 - 10)]),
                               random.randint(0, 2))

    # show the 2d top-down view
    # plt.imshow(container1.generate_top_down_view(200, 200))
    # plt.show()

    # calculate the center of gravity
    container1.draw_in_plot()
    # container1.update_center_of_gravity()

# if __name__=="__main__":

import random
import time
from enum import Enum
from itertools import combinations, product

import numpy as np
from matplotlib import pyplot as plt

import numpy
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

fig = plt.figure()
ax = Axes3D(fig, auto_add_to_figure=False)


def get_cuboid_triangulated_vertices(position: numpy.array, dimension: numpy.array):
    """
    Get the triangulated vertices of a cuboid.

    :param position: The position of the bottom left corner of the cuboid.
    :param dimension: The dimension of the cuboid.
    :return: The vertices of the cuboid.
    """
    x, y, z = position
    dx, dy, dz = dimension

    cuboid_vertices = numpy.array([
        [x, y, z],
        [x + dx, y, z],
        [x, y + dy, z],
        [x, y, z + dz],
        [x + dx, y + dy, z],
        [x + dx, y, z + dz],
        [x, y + dy, z + dz],
        [x + dx, y + dy, z + dz],

    ])

    triangles = numpy.array([
        [1, 4, 2],
        [0, 1, 2],
        [4, 2, 7],
        [6, 2, 7],
        [6, 2, 0],
        [6, 0, 3],
        [3, 1, 0],
        [3, 1, 5],
        [4, 1, 5],
        [4, 5, 7],
        [5, 3, 7],
        [3, 6, 7],
    ])

    vertices = []
    for triangle in triangles:
        vertices.append([cuboid_vertices[vertex] for vertex in triangle])
    return vertices


class Package:
    """Rectangle Package class."""

    def __init__(self, weight: float, dimensions: numpy.array, description: str = ''):
        self.weight = weight
        self.description = description
        self.dimensions = dimensions
        self.position = numpy.array([0, 0, 0], dtype=float)

    def __str__(self):
        return f'Package( {self.weight}, {self.dimensions}, {self.description})'

    def rotate(self, axis: int):
        self.dimensions = numpy.roll(self.dimensions, axis)

    def get_volume(self):
        return numpy.prod(self.dimensions)

    def plot_center(self):
        ax.scatter(self.get_center()[0], self.get_center()[1], self.get_center()[2], color='red')

    def get_center(self):
        center = self.position + self.dimensions / 2
        return center


class Container:
    """Pallet class"""

    # TODO: make numba compatible
    def __init__(self, dimensions: numpy.array, position: numpy.array,image_resolution_x: int = 100, image_resolution_y: int = 100):
        self.packages = []
        self.dimensions = dimensions
        self.position = position  # is the bottom left corner of the container
        self.total_package_weight = 0
        self.total_package_volume = 0
        self.center_of_gravity = self.get_center()
        self.highest_package = None
        self.image = numpy.zeros((image_resolution_x, image_resolution_y, 3), dtype=numpy.float32)
        self.x_map = np.linspace(0, self.dimensions[0], image_resolution_x)
        self.y_map = np.linspace(0, self.dimensions[1], image_resolution_y)

    def get_center(self):
        return self.position + self.dimensions / 2

    def add_package(self, package: Package, position_2d: numpy.array, rotation: int):
        package.rotate(rotation)
        # iterate over all packages and find the highest one over the package cross-section
        highest_package_height = 0
        highest_package = None
        for package_ in self.packages:
            cross_section_rect = numpy.array([package_.position[0],
                                              package_.position[1],
                                              package.dimensions[0],
                                              package.dimensions[1]])
            # check if the package is in the cross-section
            if cross_section_rect[0] <= position_2d[0] <= cross_section_rect[0] + cross_section_rect[2] and \
                    cross_section_rect[1] <= position_2d[1] <= cross_section_rect[1] + cross_section_rect[3]:
                if package_.position[2] >= highest_package_height:
                    highest_package_height = package_.position[2]
                    highest_package = package_
        if highest_package is not None:
            package.position = numpy.array(
                [position_2d[0], position_2d[1], highest_package_height + highest_package.dimensions[2]])
        else:
            package.position = numpy.array([position_2d[0], position_2d[1], 0])
        self.packages.append(package)
        self.total_package_weight += package.weight
        self.total_package_volume += package.get_volume()
        if self.highest_package is None or package.position[2] > self.highest_package.position[2]:
            self.highest_package = package

        self.center_of_gravity += ((
                                           package.get_center() - self.get_center()) * package.weight) / self.total_package_weight

        # update the image in the container over the cross-section of the package

        # for x in range(int(position_2d[0]), int(position_2d[0] + package.dimensions[0])):
        #     for y in range(int(position_2d[1]), int(position_2d[1] + package.dimensions[1])):

        ax.scatter(self.center_of_gravity[0], self.center_of_gravity[1],
                   self.center_of_gravity[2], color='green')

    def get_volume(self, height=None):
        if height is None:
            height = self.dimensions[2]
        return self.dimensions[0] * self.dimensions[1] * height

    def __str__(self):
        return f'Container: ({self.packages}, {self.dimensions}, {self.center_of_gravity}, {self.position})'

    def generate_top_down_view(self, resolution_x, resolution_y):
        """
        Generates a 2d image of the top-down view with the packages height in the red channel and the packages weight in
        the green channel.
        :param resolution_x: The resolution in x direction.
        :param resolution_y: The resolution in y direction.
        :return: The 2d image.
        """
        image = numpy.zeros((resolution_x, resolution_y, 3), dtype=numpy.float32)
        # ray-cast all packages for each pixel
        for index_x, x in enumerate(np.linspace(0, self.dimensions[0], resolution_x)):
            for index_y, y in enumerate(np.linspace(0, self.dimensions[1], resolution_y)):
                for package in self.packages:
                    if package.position[0] <= x <= package.position[0] + package.dimensions[0] and \
                            package.position[1] <= y <= package.position[1] + package.dimensions[1]:
                        image[index_x, index_y, 0] = (self.dimensions[2] - package.position[2]) / self.dimensions[2]
                        image[index_x, index_y, 1] = package.weight / self.total_package_weight
        return image

    def draw_in_plot(self):

        # set the limits of the plot
        ax.set_xlim3d(0, self.dimensions[0])
        ax.set_ylim3d(0, self.dimensions[1])
        ax.set_zlim3d(0, self.dimensions[2])
        fig.add_axes(ax)
        # draw the container
        ax.add_collection3d(
            Poly3DCollection(get_cuboid_triangulated_vertices(self.position, self.dimensions), facecolors='w',
                             linewidths=1, edgecolors='k', alpha=.25))

        # draw the packages in random colors
        for package in self.packages:
            ax.add_collection3d(
                Poly3DCollection(get_cuboid_triangulated_vertices(package.position + self.position, package.dimensions),
                                 facecolors=(random.random(), random.random(), random.random()), linewidths=1,
                                 edgecolors='k', alpha=.0))
            package.plot_center()
        ax.scatter(self.get_center()[0], self.get_center()[1], self.get_center()[2], c='b')
        plt.show()


class Plane:
    """Plane class"""

    def __init__(self, dimensions: numpy.array, position: numpy.array):
        self.pallets = []
        self.dimensions = dimensions
        self.position = position

    def get_volume(self):
        return numpy.prod(self.dimensions)

    def add_pallet(self, container: Container, position_2d: numpy.array):
        container.position = numpy.array([position_2d[0], position_2d[1], 0])
        self.pallets.append(container)

    def __str__(self):
        return f'Plane({self.pallets}, {self.dimensions}, {self.position})'

    def get_summed_weight(self):
        weight = 0
        for pallet in self.pallets:
            weight += pallet.get_summed_weight()
        return weight

    def calculate_center_of_gravity(self):
        center_of_gravity = numpy.array([0, 0, 0])
        for pallet in self.pallets:
            center_of_gravity += pallet.center_of_gravity * pallet.get_summed_weight()
        center_of_gravity /= self.get_summed_weight()
        return center_of_gravity


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
        self.container = Container(self.container_dimensions, numpy.array([0, 0, 0]))
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
            self.container.highest_package.position[2] + self.container.highest_package.dimensions[2])
        package_volume = self.container.total_package_volume
        distance = numpy.linalg.norm(self.container.center_of_gravity - self.target_center_of_gravity)
        self.fitness = (occupied_volume - package_volume) / distance


if __name__ == '__main__':
    # time the execution
    start_time = time.time()
    container1 = Container(numpy.array([100, 100, 100]), numpy.array([0, 0, 0]))
    # add a 100 random packages of nearly every type to the container
    for i in range(200):
        dimensions = numpy.array([random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)])
        package = Package(random.randint(1, 2), numpy.array(dimensions), f'package {i}')
        container1.add_package(package, numpy.array([random.randint(0, 100 - 10), random.randint(0, 100 - 10)]),
                               random.randint(0, 2))

    # show the 2d top-down view
    plt.imshow(container1.generate_top_down_view(200, 200))
    plt.show()

    # calculate the center of gravity
    # container1.draw_in_plot()
    # container1.update_center_of_gravity()

import random
import time
from enum import Enum
from itertools import combinations, product

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


class PackageType(Enum):
    """Package type enumeration."""
    LUGGAGE = 1
    DOCUMENT = 2
    FOOD = 3
    MEDICINE = 4
    WATER = 5


class Package:
    """Rectangle Package class."""

    def __init__(self, package_type: PackageType, weight: float, dimensions: numpy.array, description: str):
        self.package_type = package_type
        self.weight = weight
        self.description = description
        self.dimensions = dimensions
        self.position = numpy.array([0, 0, 0], dtype=float)

    def __str__(self):
        return f'Package({self.package_type}, {self.weight}, {self.dimensions}, {self.description})'

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

    def __init__(self, dimensions: numpy.array, position: numpy.array):
        self.packages = []
        self.dimensions = dimensions
        self.position = position  # is the bottom left corner of the container
        self.total_weight = 0
        self.total_volume = 0
        self.center_of_gravity = self.get_center()

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
        self.total_weight += package.weight
        self.total_volume += package.get_volume()
        self.center_of_gravity += ((package.get_center() - self.get_center()) * package.weight) / self.total_weight

        ax.scatter(self.center_of_gravity[0], self.center_of_gravity[1],
                   self.center_of_gravity[2], color='green')

    def get_volume(self):
        return numpy.prod(self.dimensions)

    def __str__(self):
        return f'Container: ({self.packages}, {self.dimensions}, {self.center_of_gravity}, {self.position})'

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


if __name__ == '__main__':
    # time the execution
    start_time = time.time()
    container1 = Container(numpy.array([100, 100, 100]), numpy.array([0, 0, 0]))
    # add a 100 random packages of nearly every type to the container
    for i in range(5):
        package_type = random.choice(list(PackageType))
        dimensions = numpy.array([random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)])
        package = Package(package_type, random.randint(1, 2), numpy.array(dimensions),
                          f'package {i}')
        container1.add_package(package, numpy.array([random.randint(0, 100 - 10), random.randint(0, 100 - 10)]),
                               random.randint(0, 2))

    # calculate the center of gravity
    container1.draw_in_plot()
    # container1.update_center_of_gravity()

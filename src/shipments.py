import itertools
from typing import Dict, List

from api_get import (Compartment, Container, ContainerType, Shipment,
                     get_container_types, get_shipments)

VOLUME_MAX_PERCENTAGE = 0.9

DEFAULT_CONTAINER_COMBINATIONS = {
    1: [
        {
            'PMC': 0,
            'PAG': 0,
            'AKE': 10,
        },
        {
            'PMC': 0,
            'PAG': 1,
            'AKE': 6,
        },
        {
            'PMC': 1,
            'PAG': 1,
            'AKE': 14,
        },

        {
            'PMC': 0,
            'PAG': 2,
            'AKE': 12,
        },
        {
            'PMC': 0,
            'PAG': 3,
            'AKE': 10,
        },
        {
            'PMC': 0,
            'PAG': 4,
            'AKE': 6,
        },
        {
            'PMC': 0,
            'PAG': 5,
            'AKE': 2,
        },
        {
            'PMC': 0,
            'PAG': 6,
            'AKE': 0,
        },
    ],
    2: [
        {
            'PMC': 0,
            'PAG': 0,
            'AKE': 20
        },
        {
            'PMC': 0,
            'PAG': 1,
            'AKE': 16
        },
        {
            'PMC': 1,
            'PAG': 1,
            'AKE': 14
        },

        {
            'PMC': 0,
            'PAG': 2,
            'AKE': 12
        },
        {
            'PMC': 0,
            'PAG': 3,
            'AKE': 10
        },
        {
            'PMC': 0,
            'PAG': 4,
            'AKE': 6,
        },
        {
            'PMC': 0,
            'PAG': 5,
            'AKE': 2
        },
        {
            'PMC': 0,
            'PAG': 6,
            'AKE': 0,
        },
    ],
    3: [
        {
            "PMC": 0,
            "PAG": 0,
            "AKE": 16,
        },
        {
            "PMC": 0,
            "PAG": 1,
            "AKE": 12,
        },
        {
            "PMC": 1,
            "PAG": 1,
            "AKE": 10,
        },
        {
            "PMC": 0,
            "PAG": 2,
            "AKE": 8,
        },
        {
            "PMC": 0,
            "PAG": 3,
            "AKE": 6,
        },
        {
            "PMC": 0,
            "PAG": 4,
            "AKE": 2,
        },
        {
            "PMC": 0,
            "PAG": 5,
            "AKE": 0,
        }
    ],
    4: [
        {
            "PMC": 0,
            "PAG": 0,
            "AKE": 16,
        },
        {
            "PMC": 0,
            "PAG": 1,
            "AKE": 12,
        },
        {
            "PMC": 1,
            "PAG": 1,
            "AKE": 10,
        },
        {
            "PMC": 0,
            "PAG": 2,
            "AKE": 8,
        },
        {
            "PMC": 0,
            "PAG": 3,
            "AKE": 6,
        },
        {
            "PMC": 0,
            "PAG": 4,
            "AKE": 2,
        },
        {
            "PMC": 0,
            "PAG": 5,
            "AKE": 0,
        }
    ],
}


def finding_closet_containers(list_of_containers: List[Container], target, depth):
    """Method to find a subset of containers with a mass closest to the target.
    Useful for fitting the mass in the compartments of a container."""
    curr_min = float('inf')
    best_subset = None
    closest = []  #list of containers with the closest mass to the target
    for subset in itertools.combinations(list_of_containers, depth):  #iterate through all combinations of containers
        weight = sum([container.weight for container in list_of_containers])
        if weight == target:  #if the sum of the weights of the containers is perfectly equal to the target, return the list of containers
            return subset
        elif weight < target and weight > curr_min:  #if the sum of the weights of the containers is less than the target and greater than the current minimum, update the current minimum and the list of containers
            curr_min = weight
            best_subset = subset
    return best_subset    #return the list of containers with the mass sum closest to the target


def sort_shipments(shipments: List[Shipment], container_types: List[ContainerType]):
    """Sort shipments by size and density, to place them more effectively"""
    shipments_dict = {}

    # sort container types by volume
    container_types.sort(key=lambda x: x.height * x.width * x.length)
    # test if the shipments fit in the AKE, else, put them in PAG or PMC
    for shipment in shipments:
        for container_type in container_types:
            if shipment.width <= container_type.width and shipment.height <= container_type.height \
                    and shipment.length <= container_type.length:
                if container_type in shipments_dict:
                    shipments_dict[container_type].append(shipment)
                else:
                    shipments_dict[container_type] = [shipment]
                break
    # sort shipments by density
    for container_type in shipments_dict:
        shipments_dict[container_type].sort(
            key=lambda _shipment: _shipment.density, reverse=True)

    return shipments_dict


def split_shipments_by_containers(shipments: List[Shipment], container_types: List[ContainerType]):
    """Split shipments by container types."""
    shipments_dict = sort_shipments(shipments, container_types)
    container_dict = {}

    for container_type in shipments_dict:
        container_dict[container_type] = []
        current_container = Container(container_type)
        container_dict[container_type].append(current_container)
        for shipment in shipments_dict[container_type]:
            if current_container.occupied_volume + shipment.volume > container_type.volume * VOLUME_MAX_PERCENTAGE:
                current_container = Container(container_type)
                current_container.add_shipment(shipment)
                container_dict[container_type].append(current_container)
            current_container.add_shipment(shipment)

    return container_dict


def split_containers_by_compartments(container_dict: Dict[ContainerType, List[Container]], compartments: List[Compartment]):
    """Split containers by compartments."""
    compartments_dict = {}
    # sort compartments by compartment_id
    compartments.sort(key=lambda x: x.compartment_id, reverse=True)

    # start filling compartments with the highest compartment_id
    for compartment in compartments:
        container_combinations = DEFAULT_CONTAINER_COMBINATIONS[compartment.compartment_id]


# find the containers that add up the closest to the max_weight of the compartment
if __name__ == '__main__':
    # # Get all shipments
    # shipments = get_shipments()
    # # Get all container types
    # container_types = get_container_types()
    # # Sort shipments by size
    # sorted_shipments = sort_shipments(shipments, container_types)
    # # Split shipments by container types
    # split_shipments = split_shipments_by_containers(shipments, container_types)
    #
    # pass

    # Test n_sum
    arr = [1, 2.2, 3, 4.6, 5.2, 6.123, 7.1, 84, 9, 120]
    print(finding_closet_containers(arr, 14, 10),
          sum(finding_closet_containers(arr, 14, 10)))

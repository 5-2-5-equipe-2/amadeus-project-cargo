import itertools
import random
from typing import Dict, List
from api_get import (Container, ContainerType, Shipment, get_container_types,
                     get_shipments, Compartment, LotOfLuggage, DEFAULT_CONTAINER_COMBINATIONS, get_luggage,
                     DEFAULT_COMPARTMENTS_MAX_WEIGHT, get_compartments)
from tqdm import tqdm
import copy

VOLUME_MAX_PERCENTAGE = 0.9


def finding_closet_containers(list_of_containers: List[Container], target, depth):
    """Method to find a subset of containers with a mass closest to the target.
    Useful for fitting the mass in the compartments of a container."""
    curr_min = float('inf')
    best_subset = None
    # iterate through all combinations of containers
    for subset in itertools.combinations(list_of_containers, depth):
        weight = sum([container.weight for container in list_of_containers])
        # if the sum of the weights of the containers is perfectly equal to the target, return the list of containers
        if weight == target:
            return best_subset
        # if the sum of the weights of the containers is less than the target,
        # but greater than the current minimum, update the current minimum
        if target > weight > curr_min:
            curr_min = weight
            best_subset = subset
    return best_subset


def find_best_container_combination(container_dict_copy: Dict[ContainerType, List[Container]],
                                    combinations: [Dict[str, int]],
                                    weight_target: float,
                                    ):
    """Find the best container combination for a compartment."""

    def try_combination():
        # find calculate the max weight of each combination
        combinations_max_weight = {}
        for combination in combinations:
            max_weight = 0
            combinations_max_weight[str(combination)] = {}
            for container_type in container_dict_copy.keys():
                densest_containers = random.choices(container_dict_copy[container_type],
                                                    k=combination[container_type.container_type])
                max_weight += sum([container.weight for container in densest_containers])
                combinations_max_weight[str(combination)][container_type] = densest_containers

            combinations_max_weight[str(combination)]["max_weight"] = max_weight
        # find the combination with the max weight closest to the target without exceeding it
        best_combination = None
        curr_max1 = float('-inf')
        for combination in combinations_max_weight:
            if weight_target > combinations_max_weight[combination]["max_weight"] > curr_max1:
                curr_max1 = combinations_max_weight[combination]["max_weight"]
                best_combination = combinations_max_weight[combination]

        return best_combination

    # find the best combination closest to the target without exceeding it
    number_of_tries = 1000
    best_combination = None
    curr_max = float('-inf')
    for _ in tqdm(range(number_of_tries)):
        combination = try_combination()
        if combination:
            if curr_max < combination["max_weight"] <= weight_target:
                curr_max = combination["max_weight"]
                best_combination = combination

    return best_combination


def sort_shipments(shipments: List[Shipment], container_types: List[ContainerType]):
    """Sort shipments by size and density, to place them more effectively"""
    shipments_dict = {}

    # sort container types by volume
    container_types.sort(key=lambda x: x.height * x.width * x.length)
    # test if the shipments fit in the AKE, else, put them in PAG or PMC
    for shipment in shipments:
        for container_type in container_types:
            if shipment.width <= container_type.width \
                    and shipment.height <= container_type.height \
                    and shipment.length <= container_type.length \
                    and shipment.weight <= (container_type.max_weight - container_type.tare_weight):
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
            if current_container.occupied_volume + shipment.volume > container_type.volume * VOLUME_MAX_PERCENTAGE \
                    or current_container.weight + shipment.weight > container_type.max_weight:
                current_container = Container(container_type)
                current_container.add_shipment(shipment)
                container_dict[container_type].append(current_container)
            current_container.add_shipment(shipment)
    return container_dict


def split_containers_by_compartments(container_dict: Dict[ContainerType, List[Container]],
                                     compartments: List[Compartment]):
    """Split containers by compartments."""
    compartments_dict = {}
    # sort compartments by compartment_id
    compartments.sort(key=lambda x: x.compartment_id, reverse=True)

    # start filling compartments with the highest compartment_id
    containers_combination_small = find_best_container_combination(container_dict, [{"AKE": 2, "PAG": 0, "PMC": 0}],
                                                                   2635)

    containers_combination_aft = find_best_container_combination(container_dict,
                                                                 DEFAULT_CONTAINER_COMBINATIONS["AFT"],
                                                                 DEFAULT_COMPARTMENTS_MAX_WEIGHT["AFT"])

    containers_combination_fwd = find_best_container_combination(container_dict,
                                                                 DEFAULT_CONTAINER_COMBINATIONS["FWD"],
                                                                 DEFAULT_COMPARTMENTS_MAX_WEIGHT["FWD"])

    return containers_combination_small, containers_combination_aft, containers_combination_fwd, container_dict


# find the containers that add up the closest to the max_weight of the compartment
if __name__ == '__main__':
    # Get all shipments
    shipments = get_shipments()
    # Get all container types
    container_types: [ContainerType] = get_container_types()
    # container_types = list(filter(lambda x: x.container_type != "PAG", container_types))
    # Sort shipments by size
    sorted_shipments = sort_shipments(shipments, container_types)
    # Split shipments by container types
    containers = split_shipments_by_containers(shipments, container_types)
    # add luggage to containers

    luggage = get_luggage()
    containers[luggage.container_type].extend(luggage.containers)
    best = split_containers_by_compartments(containers, get_compartments())

    # filter container for the small ones
    # container_copy = containers.copy()
    # for container_type in container_copy:
    #     if container_type.container_type == "PAG" or container_type.container_type == "PMC":
    #         container_copy[container_type] = []
    #     else:
    #         container_copy[container_type] = list(filter(lambda x: x.weight < 2000, containers[container_type]))
    #
    # best = find_best_container_combination(container_copy, [{"AKE": 2, "PAG": 0, "PMC": 0}], 2635)
    # best = find_best_container_combination(containers, DEFAULT_CONTAINER_COMBINATIONS["AFT"],
    #                                        DEFAULT_COMPARTMENTS_MAX_WEIGHT["AFT"])
    pass

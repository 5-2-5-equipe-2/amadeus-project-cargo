import itertools
from typing import Dict, List
from api_get import (Container, ContainerType, Shipment, get_container_types,
                     get_shipments, Compartment, LotOfLuggage, DEFAULT_CONTAINER_COMBINATIONS, get_luggage,
                     DEFAULT_COMPARTMENTS_MAX_WEIGHT)
from tqdm import tqdm

VOLUME_MAX_PERCENTAGE = 0.9


def finding_closet_containers(list_of_containers: List[Container], target, depth):
    """Method to find a subset of containers with a mass closest to the target.
    Useful for fitting the mass in the compartments of a container."""
    curr_min = float('inf')
    best_subset = None
    for subset in itertools.combinations(list_of_containers, depth):  # iterate through all combinations of containers
        weight = sum([container.weight for container in list_of_containers])
        if weight == target:  # if the sum of the weights of the containers is perfectly equal to the target, return the list of containers
            return best_subset
        if target > weight > curr_min:  # if the sum of the weights of the containers is less than the target, but greater than the current minimum, update the current minimum
            curr_min = weight
            best_subset = subset
    return best_subset


def find_best_container_combination(container_dict: Dict[ContainerType, List[Container]],
                                    combinations: [Dict[str, int]],
                                    weight_target: float,
                                    ):
    """Find the best container combination for a compartment."""
    # order container types by density
    container_dict_copy = container_dict.copy()
    for container_type in container_dict_copy:
        container_dict_copy[container_type].sort(key=lambda x: x.weight, reverse=True)

    # find calculate the max weight of each combination
    combinations_max_weight = {}
    for combination in combinations:
        max_weight = 0
        combinations_max_weight[str(combination)] = {}
        for container_type in container_dict.keys():
            densest_containers = container_dict[container_type][:combination[container_type.container_type]]
            max_weight += sum([container.weight for container in densest_containers])
            combinations_max_weight[str(combination)][container_type] = densest_containers

        combinations_max_weight[str(combination)]["max_weight"] = max_weight
    # find the combination with the max weight closest to the target
    best_combination = None
    curr_min = float('inf')
    for combination in combinations_max_weight:
        if weight_target > combinations_max_weight[combination]["max_weight"] > curr_min:
            curr_min = combinations_max_weight[combination]["max_weight"]
            best_combination = combination
    return combinations_max_weight[best_combination]

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
    for compartment in compartments:
        compartment_combinations = None
        if compartment.compartment_id < 3:
            compartment_combinations = DEFAULT_CONTAINER_COMBINATIONS["FWD"]
        else:
            compartment_combinations = DEFAULT_CONTAINER_COMBINATIONS["AFT"]

        # for container_combination in compartment_combinations:
        #     # get the list of containers for the current combination
        #     container_list = []
        #     for container_type in container_combination:
        #         if container_type in container_dict:
        #             container_list.extend(container_dict[container_type])
        #     # sort the list of containers by weight
        #     container_list.sort(key=lambda x: x.weight, reverse=True)
        #     # find the subset of containers with the closest mass to the target
        #     target = compartment.max_weight
        #     depth = compartment.max_containers
        #     closest_containers = finding_closet_containers(container_list, target, depth)
        #     if closest_containers is not None:
        #         if compartment in compartments_dict:
        #             compartments_dict[compartment].append(closest_containers)
        #         else:
        #             compartments_dict[compartment] = [closest_containers]
        #         break


# find the containers that add up the closest to the max_weight of the compartment
if __name__ == '__main__':
    # Get all shipments
    shipments = get_shipments()
    # Get all container types
    container_types: [ContainerType] = get_container_types()
    container_types = list(filter(lambda x: x.container_type != "PAG", container_types))
    # Sort shipments by size
    sorted_shipments = sort_shipments(shipments, container_types)
    # Split shipments by container types
    containers = split_shipments_by_containers(shipments, container_types)
    # add luggage to containers
    luggage = get_luggage()
    containers[luggage.container_type].extend(luggage.containers)

    best = find_best_container_combination(containers, DEFAULT_CONTAINER_COMBINATIONS["FWD"],
                                           DEFAULT_COMPARTMENTS_MAX_WEIGHT["FWD"])

    pass

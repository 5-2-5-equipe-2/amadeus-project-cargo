from typing import Dict, List

import itertools
from api_get import (Container, ContainerType, Shipment, get_container_types,
                     get_shipments, Compartment, LotOfLuggage, DEFAULT_CONTAINER_COMBINATIONS, get_luggage)

VOLUME_MAX_PERCENTAGE = 0.9


def finding_closet_containers(list_of_containers: List[Container], target, depth):
    closest = []
    for subset in itertools.combinations(list_of_containers, depth):
        if sum([container.weight for container in list_of_containers]) == target:
            return subset
        else:
            closest.append((abs(sum([container.weight for container in list_of_containers]) - target), subset))
    return min(closest)[1]


def sort_shipments(shipments: List[Shipment], container_types: List[ContainerType]):
    """Sort shipments by size."""
    shipments_dict = {}

    # sort container types by volume
    container_types.sort(key=lambda x: x.height * x.width * x.length)

    for shipment in shipments:
        for container_type in container_types:
            if shipment.width <= container_type.width \
                    and shipment.height <= container_type.height \
                    and shipment.length <= container_type.length \
                    and shipment.weight <= container_type.max_weight - container_type.tare_weight:
                if container_type in shipments_dict:
                    shipments_dict[container_type].append(shipment)
                else:
                    shipments_dict[container_type] = [shipment]
                break

    for container_type in shipments_dict:
        shipments_dict[container_type].sort(key=lambda _shipment: _shipment.density, reverse=True)

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


def split_containers_by_compartments(container_dict: Dict[ContainerType, List[Container]], compartments: [Compartment]):
    """Split containers by compartments."""
    compartments_dict = {}
    # sort compartments by compartment_id
    compartments.sort(key=lambda x: x.compartment_id, reverse=True)

    # start filling compartments with the highest compartment_id
    for compartment in compartments:
        container_combinations = DEFAULT_CONTAINER_COMBINATIONS[compartment.compartment_id]


# find the containers that add up the closest to the max_weight of the compartment
if __name__ == '__main__':
    # Get all shipments
    shipments = get_shipments()
    # Get all container types
    container_types = get_container_types()
    # Sort shipments by size
    sorted_shipments = sort_shipments(shipments, container_types)
    # Split shipments by container types
    containers = split_shipments_by_containers(shipments, container_types)
    # add luggage to containers
    luggage = get_luggage()
    containers[luggage.container_type].extend(luggage.containers)

    pass

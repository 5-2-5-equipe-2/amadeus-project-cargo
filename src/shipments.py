from typing import Dict, List

from api_get import get_container_types, ContainerType, get_shipments, Shipment, Container

VOLUME_MAX_PERCENTAGE = 0.9


def sort_shipments(shipments: [Shipment], container_types: [ContainerType]):
    """Sort shipments by size."""
    shipments_dict = {}

    # sort container types by volume
    container_types.sort(key=lambda x: x.height * x.width * x.length)

    for shipment in shipments:
        for container_type in container_types:
            if shipment.width <= container_type.width and shipment.height <= container_type.height \
                    and shipment.length <= container_type.length:
                if container_type in shipments_dict:
                    shipments_dict[container_type].append(shipment)
                else:
                    shipments_dict[container_type] = [shipment]
                break

    for container_type in shipments_dict:
        shipments_dict[container_type].sort(key=lambda _shipment: _shipment.density, reverse=True)

    return shipments_dict


def split_shipments_by_containers(shipments: [Shipment], container_types: [ContainerType]):
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


if __name__ == '__main__':
    # Get all shipments
    shipments = get_shipments()
    # Get all container types
    container_types = get_container_types()
    # Sort shipments by size
    sorted_shipments = sort_shipments(shipments, container_types)
    # Split shipments by container types
    split_shipments = split_shipments_by_containers(shipments, container_types)

    pass

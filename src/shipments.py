from typing import Dict, List

from api_get import get_container_types, ContainerType, get_shipments, Shipment


def sort_shipments(shipments: [Shipment], container_types: [ContainerType]):
    """Sort shipments by size."""
    shipments_dict = {}

    # sort container types by volume
    container_types.sort(key=lambda x: x.height * x.width * x.length)

    for shipment in shipments:
        for container_type in container_types:
            if shipment.width <= container_type.width and shipment.height <= container_type.height \
                    and shipment.length <= container_type.length:
                if container_type.container_type in shipments_dict:
                    shipments_dict[container_type.container_type].append(shipment)
                else:
                    shipments_dict[container_type.container_type] = [shipment]
                break

    for container_type in shipments_dict:
        shipments_dict[container_type].sort(key=lambda _shipment: _shipment.density, reverse=True)

    return shipments_dict


if __name__ == '__main__':
    # Get all shipments
    shipments = get_shipments()
    # Get all container types
    container_types = get_container_types()
    # Sort shipments by size
    sorted_shipments = sort_shipments(shipments, container_types)
    # Print sorted shipments
    pass

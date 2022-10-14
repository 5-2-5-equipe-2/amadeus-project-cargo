from api_get import get_container_types


class Shipment:
    """Rectangle Shipment class."""

    def __init__(self, weight: float, height, width, length, awb):
        self.shipment_id = awb
        self.weight = weight
        self.awb = awb
        self.volume = height * width * length

    def __str__(self):
        return f'Shipment( {self.weight}, {self.volume}, {self.awb})'




def sort_shipments(shipments):
    """Sort shipments by weight."""
    container_types = get_container_types()



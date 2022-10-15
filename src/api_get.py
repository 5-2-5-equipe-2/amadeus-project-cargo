import base64
from functools import lru_cache
from typing import List

import requests

# GET https://af-cargo-api-cargo.azuremicroservices.io/api/compartment to retrieve all compartments
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/container to retrieve all container types
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/shipment to retrieve all shipments
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/luggage to retrieve nb of Luggage and average weight
# POST https://af-cargo-api-cargo.azuremicroservices.io/api/submit to submit your answer with an object containing the 5 compartment with their containers and shipments (shipment id list).
# POST http://localhost:8081/api/graph to transform the solution into the image (base64 encoded)
DEFAULT_LUGGAGE_CONTAINER = 'AKE'
DEFAULT_NB_LUGGAGE_PER_CONTAINER = 38
DEFAULT_CONTAINER_TARE_WEIGHT = {
    "PMC": 120,
    "PAG": 125,
    "AKE": 57,
}

DEFAULT_CONTAINER_MAX_WEIGHT = {
    "PMC": 5102,
    "PAG": 4676,
    "AKE": 1587,
}

DEFAULT_COMPARTMENTS_MAX_WEIGHT = {
    "FWD": 32005,
    "AFT": 25655,
}

DEFAULT_CONTAINER_COMBINATIONS = {
    "FWD": [
        {
            'PAG': 0,
            'PMC': 0,
            'AKE': 20
        },
        {
            'PAG': 0,
            'PMC': 1,
            'AKE': 16
        },
        {
            'PAG': 1,
            'PMC': 1,
            'AKE': 14
        },

        {
            'PAG': 0,
            'PMC': 2,
            'AKE': 12
        },
        {
            'PAG': 0,
            'PMC': 3,
            'AKE': 10
        },
        {
            'PAG': 0,
            'PMC': 4,
            'AKE': 6,
        },
        {
            'PAG': 0,
            'PMC': 5,
            'AKE': 2
        },
        {
            'PAG': 0,
            'PMC': 6,
            'AKE': 0,
        },
    ],

    "AFT": [
        {
            "PAG": 0,
            "PMC": 0,
            "AKE": 16,
        },
        {
            "PAG": 0,
            "PMC": 1,
            "AKE": 12,
        },
        {
            "PAG": 1,
            "PMC": 1,
            "AKE": 10,
        },
        {
            "PAG": 0,
            "PMC": 2,
            "AKE": 8,
        },
        {
            "PAG": 0,
            "PMC": 3,
            "AKE": 6,
        },
        {
            "PAG": 0,
            "PMC": 4,
            "AKE": 2,
        },
        {
            "PAG": 0,
            "PMC": 5,
            "AKE": 0,
        }
    ],

}

DEFAULT_MAX_CONTAINERS_BY_COMPARTMENT = {
    1: [{
        "PMC" : 3,
        "PAG" : 0,
        "AKE" : 2
    },
    {
        "PMC" : 2,
        "PAG" : 0,
        "AKE" : 2
    },
    {
        "PMC" : 1,
        "PAG" : 0,
        "AKE" : 6
    }],
    2: [{
        "PMC" : 3,
        "PAG" : 0,
        "AKE" : 0
    },
    {
        "PMC" : 2,
        "PAG" : 0,
        "AKE" : 2
    },
    {
        "PMC" : 1,
        "PAG" : 1,
        "AKE" : 4
    }],
    3: [{
        "PMC" : 3,
        "PAG" : 0,
        "AKE" : 0
    },
    {
        "PMC" : 2,
        "PAG" : 0,
        "AKE" : 0
    },
    {
        "PMC" : 1,
        "PAG" : 1,
        "AKE" : 2
    }],
    4: [{
        "PMC" : 2,
        "PAG" : 0,
        "AKE" : 0
    },
    {
        "PMC" : 1,
        "PAG" : 0,
        "AKE" : 4
    },
    {
        "PMC" : 0,
        "PAG" : 0,
        "AKE" : 8
    }],
}

class Shipment:
    """Rectangle Shipment class."""

    def __init__(self, weight: float, height, width, length, awb, id = 1):
        self.shipment_id = awb
        self.weight = weight
        self.awb = awb
        self.width = width
        self.height = height
        self.length = length
        self.volume = self.width * self.height * self.length
        self.density = self.weight / self.volume
        self.id = id

    def __str__(self):
        return f'Shipment({self.shipment_id}, {self.weight}, {self.width}, {self.height}, {self.length}, {self.volume}, {self.density})'


class ContainerType:
    container_type_id = 0

    def __init__(self, container_type, height, width, length, max_weight, tare_weight):
        Container.container_id += 1
        self.container_type_id = Container.container_id
        self.container_type = container_type
        self.height = height
        self.width = width
        self.length = length
        self.volume = self.width * self.height * self.length
        self.max_weight = max_weight
        self.tare_weight = 0

    def __str__(self):
        return f'ContainerType({self.container_type}, {self.height}, {self.width}, {self.length})'


class Compartment:
    def __init__(self, compartment_id, max_weight):
        self.compartment_id = compartment_id
        # self.height = height
        # self.width = width
        # self.length = length
        self.containers = []
        self.max_weight = max_weight
        self.weight = 0
        self.combinations = None

    def add_container(self, container):
        self.containers.append(container)
        self.weight += container.weight

    def __str__(self):
        return f'Compartment({self.compartment_id}, {self.max_weight}, {self.containers})'


class Container:
    container_id = 0

    def __init__(self, container_type: ContainerType, is_required=False):
        Container.container_id += 1
        self.container_id = Container.container_id
        self.container_type = container_type
        self.shipments = []
        self.occupied_volume = 0
        self.weight = container_type.tare_weight
        self.occupied_volume_percentage = 0
        self.is_required = is_required
        self.density = 0

    def add_shipment(self, shipment: Shipment):
        self.shipments.append(shipment)
        self.occupied_volume += shipment.volume
        self.weight += shipment.weight
        self.occupied_volume_percentage = self.occupied_volume / self.container_type.volume
        self.density = self.weight / self.container_type.volume

    def full_luggage(self):
        return self.occupied_volume_percentage == 1

    def __str__(self):
        return f'Container({self.container_id} , {self.is_required=}, {self.density=}, {self.container_type=}, {self.weight=}, {self.occupied_volume_percentage=}, {self.occupied_volume=})'


class LotOfLuggage:  # class for the luggage, a type of shipment

    def __init__(self, first_class_luggage, nb_luggage, avg_weight, container_type, number_of_luggage_by_container):
        self.number_of_luggage_per_container = number_of_luggage_by_container
        self.avg_weight = avg_weight
        self.container_type = container_type
        self.containers = LotOfLuggage.split_luggage_into_containers(
            nb_luggage - first_class_luggage, avg_weight, container_type, number_of_luggage_by_container
        ) + LotOfLuggage.split_luggage_into_containers(
            first_class_luggage, avg_weight, container_type, number_of_luggage_by_container
        )
        self.total_weight = sum([container.weight for container in self.containers])

    @staticmethod
    def split_luggage_into_containers(nb_luggage, avg_weight, container_type, number_of_luggage_by_container):
        number_of_containers = int(nb_luggage / number_of_luggage_by_container)
        remaining_luggage = nb_luggage % number_of_luggage_by_container
        containers = []
        for _ in range(number_of_containers):
            container = Container(container_type, is_required=True)
            container.weight = avg_weight * number_of_luggage_by_container
            container.occupied_volume = container.container_type.volume
            container.occupied_volume_percentage = 1
            container.density = container.weight / container.container_type.volume
            container.nb_luggage = number_of_luggage_by_container
            containers.append(container)
        if remaining_luggage > 0:
            container = Container(container_type)
            container.weight = avg_weight * remaining_luggage
            container.occupied_volume = container.container_type.volume * (
                    remaining_luggage / number_of_luggage_by_container)
            container.occupied_volume_percentage = container.occupied_volume / container.container_type.volume
            container.density = container.weight / container.container_type.volume
            container.nb_luggage = remaining_luggage
            containers.append(container)
        return containers


@lru_cache(maxsize=None)
def get_compartments():
    """Get all compartments from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/compartment").json()
    return [Compartment(compartment["compartmentId"], compartment["maxWeight"]) for compartment in response]


@lru_cache(maxsize=None)
def get_container_types():
    """Get all container types from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/container")
    return [ContainerType(container_type["type"],
                          container_type["height"],
                          container_type["width"],
                          container_type["length"],
                          DEFAULT_CONTAINER_MAX_WEIGHT[container_type["type"]],
                          DEFAULT_CONTAINER_TARE_WEIGHT[container_type["type"]])
            for container_type
            in response.json()]


@lru_cache(maxsize=None)
def get_shipments():
    """Get all shipments from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/shipment")
    return [Shipment(shipment["weight"], shipment["height"], shipment["width"], shipment["length"], shipment["awb"],shipment["id"]) for
            shipment in response.json()]


@lru_cache(maxsize=None)
def get_luggage():
    """Get all shipments from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/luggage").json()
    return LotOfLuggage(response["nbFirstClassLuggage"], response["nbLuggage"], response["avgWeight"],
                        list(filter(lambda x: x.container_type == DEFAULT_LUGGAGE_CONTAINER, get_container_types()))[0],
                        DEFAULT_NB_LUGGAGE_PER_CONTAINER)


def submit_solution(solution=
                    [{"compartmentId": 1, "containersWithShipments": [
                        {"containerType": "PMC", "shipments": [1, 3, 4, 4, 6, 7, 8, 9, 10, 11, 12, 12]},
                        {"containerType": "PAG", "shipments": [5]}, {"containerType": "AKE", "shipments": [7]}],
                      "containersWithLuggage": [{"containerType": "AKE", "nbOfLuggage": 30},
                                                {"containerType": "AKE", "nbOfLuggage": 38}]},
                     {"compartmentId": 2,
                      "containersWithShipments": [{"containerType": "PMC", "shipments": [2]},
                                                  {"containerType": "PAG", "shipments": [4, 6]},
                                                  {"containerType": "AKE", "shipments": [9]}],
                      "containersWithLuggage": [{"containerType": "AKE", "nbOfLuggage": 38},
                                                {"containerType": "AKE", "nbOfLuggage": 38},
                                                {"containerType": "AKE", "nbOfLuggage": 38},
                                                {"containerType": "AKE", "nbOfLuggage": 38},
                                                {"containerType": "AKE", "nbOfLuggage": 38},
                                                {"containerType": "AKE", "nbOfLuggage": 38}]},
                     {"compartmentId": 3,
                      "containersWithShipments": [{"containerType": "PMC", "shipments": [8, 10]},
                                                  {"containerType": "PAG", "shipments": [11]},
                                                  {"containerType": "AKE", "shipments": [14]}]},
                     {"compartmentId": 4,
                      "containersWithShipments": [{"containerType": "PMC", "shipments": [13]},
                                                  {"containerType": "PAG", "shipments": [12]},
                                                  {"containerType": "AKE", "shipments": [14]}]},
                     {"compartmentId": 5,
                      "containersWithLuggage": [{"containerType": "AKE", "nbOfLuggage": 25}]}]):
    """Submit solution to API."""
    response = requests.post("https://af-cargo-api-cargo.azuremicroservices.io/api/submit", json=solution)
    return response.json()


def get_graph(solution={"law": 167608.3, "warnings": [
    {"error": {"code": "WARN01", "message": "The submitted shipment list is not complete. You forgot 84 shipments"},
     "stackTrace": [], "suppressedExceptions": []}], "zfwCg": 52.00591, "toCg": 48.00749, "zfw": 160009.3,
                        "fwdLimit": 28.718961908839653, "aftLimit": 85.90082412664209, "tow": 228225.3,
                        "ldCg": 52.63887}):
    """Get graph from API as a base64 image and write it to output.png"""
    response = requests.post("http://localhost:8081/api/graph", json=solution)

    print(response.json())
    g = open("output.png", "wb")
    g.write(base64.b64decode(response.json()["graph.png"]))
    g.close()


def test_solution():
    """Test solution."""
    print(get_compartments())
    print(get_container_types())
    print(get_shipments())
    print(get_luggage())
    print(submit_solution())
    get_graph()


if __name__ == "__main__":
    test_luggage = get_luggage()
    test_shipments = get_shipments()
    test_container_types = get_container_types()
    test_compartments = get_compartments()
    test_solution()

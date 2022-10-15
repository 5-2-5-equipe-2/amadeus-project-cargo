
import base64
from typing import List

import requests

# GET https://af-cargo-api-cargo.azuremicroservices.io/api/compartment to retrieve all compartments
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/container to retrieve all container types
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/shipment to retrieve all shipments
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/luggage to retrieve nb of Luggage and average weight
# POST https://af-cargo-api-cargo.azuremicroservices.io/api/submit to submit your answer with an object containing the 5 compartment with their containers and shipments (shipment id list).
# POST http://localhost:8081/api/graph to transform the solution into the image (base64 encoded)

class Shipment:
    """Rectangle Shipment class."""

    def __init__(self, weight: float, height, width, length, awb):
        self.shipment_id = awb
        self.weight = weight
        self.awb = awb
        self.width = width
        self.height = height
        self.length = length
        self.volume = self.width * self.height * self.length
        self.density = self.weight / self.volume

    def __str__(self):
        return f'Shipment({self.shipment_id}, {self.weight}, {self.width}, {self.height}, {self.length}, {self.volume}, {self.density})'


class ContainerType:
    def __init__(self, container_type, height, width, length):
        self.container_type = container_type
        self.height = height
        self.width = width
        self.length = length
        self.volume = self.width * self.height * self.length

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

    def add_container(self, container):
        self.containers.append(container)
        self.weight += container.weight

    def __str__(self):
        return f'Compartment({self.compartment_id}, {self.max_weight}, {self.containers})'


class Container:
    def __init__(self, container_type):
        self.container_type = container_type
        self.shipments = []
        self.occupied_volume = 0
        self.weight = 0
        self.occupied_volume_percentage = 0

    def add_shipment(self, shipment: Shipment):
        self.shipments.append(shipment)
        self.occupied_volume += shipment.volume
        self.weight += shipment.weight
        self.occupied_volume_percentage = self.occupied_volume / self.container_type.volume

    def full_luggage(self):
        return self.occupied_volume_percentage == 1

    def __str__(self):
        return f'Container({self.container_type},{self.weight}, {self.occupied_volume_percentage}, {self.occupied_volume})'


class LotOfLuggage(Shipment): #class for the luggage, a type of shipment
    avg_weight = 20 #average weight of a luggage
    nb_luggage = 38 #number of luggage fitting in a AKE container
    def __init__(self, nb_luggage : int=nb_luggage, avg_weight : float=avg_weight):
        super().__init__(avg_weight*nb_luggage, 1000, 1000, 1000, 'Luggage') #the luggages must fill the container

    @staticmethod
    def placeLuggages(nbluggages : int) -> List[Container]:      #method to create the containers needed to fit the luggages
        list_containers = []
        while nbluggages > 0:
            luggages = LotOfLuggage(nbluggages)
            ake=Container(ContainerType('AKE', 1000, 1000, 1000))
            ake.add_shipment(luggages)
            list_containers.append(ake)
        return list_containers

def get_compartments():
    """Get all compartments from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/compartment")
    return response.json()


def get_container_types():
    """Get all container types from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/container")
    return [ContainerType(container_type["type"], container_type["height"], container_type["width"],
                          container_type["length"]) for container_type in response.json()]


def get_shipments():
    """Get all shipments from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/shipment")
    return [Shipment(shipment["weight"], shipment["height"], shipment["width"], shipment["length"], shipment["awb"]) for
            shipment in response.json()]


def get_luggage():
    """Get all shipments from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/luggage")
    return response.json()


def submit_solution(solution = [{"compartmentId":1, "containersWithShipments": [{"containerType":"PMC","shipments":[1,3,4,4,6,7,8,9,10,11,12,12]},{"containerType":"PAG","shipments":[5]},{"containerType":"AKE","shipments":[7]}], "containersWithLuggage": [{"containerType":"AKE","nbOfLuggage":30},{"containerType":"AKE","nbOfLuggage":38}]},{"compartmentId":2, "containersWithShipments": [{"containerType":"PMC","shipments":[2]},{"containerType":"PAG","shipments":[4,6]},{"containerType":"AKE","shipments":[9]}], "containersWithLuggage": [{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38}]},{"compartmentId":3, "containersWithShipments": [{"containerType":"PMC","shipments":[8,10]},{"containerType":"PAG","shipments":[11]},{"containerType":"AKE","shipments":[14]}]},{"compartmentId":4, "containersWithShipments": [{"containerType":"PMC","shipments":[13]},{"containerType":"PAG","shipments":[12]},{"containerType":"AKE","shipments":[14]}]},{"compartmentId":5, "containersWithLuggage": [{"containerType":"AKE","nbOfLuggage":25}]}]):
    """Submit solution to API."""
    response = requests.post("https://af-cargo-api-cargo.azuremicroservices.io/api/submit", json=solution)
    return response.json()


def get_graph(solution = {"law":167608.3,"warnings":[{"error":{"code":"WARN01","message":"The submitted shipment list is not complete. You forgot 84 shipments"},"stackTrace":[],"suppressedExceptions":[]}],"zfwCg":52.00591,"toCg":48.00749,"zfw":160009.3,"fwdLimit":28.718961908839653,"aftLimit":85.90082412664209,"tow":228225.3,"ldCg":52.63887}):
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
    test_solution()

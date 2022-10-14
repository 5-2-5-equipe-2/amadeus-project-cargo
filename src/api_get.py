"""module to get data from API with get and post."""
import graphlib
import requests
import base64

# GET https://af-cargo-api-cargo.azuremicroservices.io/api/compartment to retrieve all compartments
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/container to retrieve all container types
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/shipment to retrieve all shipments
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/luggage to retrieve nb of Luggage and average weight
# POST https://af-cargo-api-cargo.azuremicroservices.io/api/submit to submit your answer with an object containing the 5 compartment with their containers and shipments (shipment id list).
# POST http://localhost:8081/api/graph to transform the solution into the image (base64 encoded)


def get_compartments():
    """Get all compartments from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/compartment")
    return response.json()


def get_container_types():
    """Get all container types from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/container")
    return response.json()


def get_shipments():
    """Get all shipments from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/shipment")
    return response.json()


def get_luggage():
    """Get all shipments from API."""
    response = requests.get("https://af-cargo-api-cargo.azuremicroservices.io/api/luggage")
    return response.json()


def submit_solution(solution):
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

def test_solution(solution = [{"compartmentId":1, "containersWithShipments": [{"containerType":"PMC","shipments":[1,3,4,4,6,7,8,9,10,11,12,12]},{"containerType":"PAG","shipments":[5]},{"containerType":"AKE","shipments":[7]}], "containersWithLuggage": [{"containerType":"AKE","nbOfLuggage":30},{"containerType":"AKE","nbOfLuggage":38}]},{"compartmentId":2, "containersWithShipments": [{"containerType":"PMC","shipments":[2]},{"containerType":"PAG","shipments":[4,6]},{"containerType":"AKE","shipments":[9]}], "containersWithLuggage": [{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38},{"containerType":"AKE","nbOfLuggage":38}]},{"compartmentId":3, "containersWithShipments": [{"containerType":"PMC","shipments":[8,10]},{"containerType":"PAG","shipments":[11]},{"containerType":"AKE","shipments":[14]}]},{"compartmentId":4, "containersWithShipments": [{"containerType":"PMC","shipments":[13]},{"containerType":"PAG","shipments":[12]},{"containerType":"AKE","shipments":[14]}]},{"compartmentId":5, "containersWithLuggage": [{"containerType":"AKE","nbOfLuggage":25}]}]):
    """Test solution."""
    print(get_compartments())
    print(get_container_types())
    print(get_shipments())
    print(get_luggage())
    print(submit_solution(solution))
    get_graph()

if __name__ == "__main__":
    test_solution()


import requests


# GET https://af-cargo-api-cargo.azuremicroservices.io/api/compartment to retrieve all compartments
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/container to retrieve all container types
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/shipment to retrieve all shipments
# GET https://af-cargo-api-cargo.azuremicroservices.io/api/luggage to retrieve nb of Luggage and average weight
# POST https://af-cargo-api-cargo.azuremicroservices.io/api/submit to submit your answer with an object containing the 5 compartment with their containers and shipments (shipment id list).
#


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

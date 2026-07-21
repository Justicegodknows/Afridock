from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/health.feature")


@given("the API application", target_fixture="app_client")
def app_client(client: TestClient) -> TestClient:
    return client


@when(parsers.parse('a client requests "{path}"'), target_fixture="response")
def response(app_client: TestClient, path: str):
    return app_client.get(path)


@then(parsers.parse("the response status is {status:d}"))
def check_status(response, status: int) -> None:
    assert response.status_code == status


@then(parsers.parse('the response body reports status "{expected_status}"'))
def check_body(response, expected_status: str) -> None:
    assert response.json()["status"] == expected_status

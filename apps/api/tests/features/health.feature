Feature: Engineering foundation ready
  A new engineer can build and ship on day one.

  Scenario: API health endpoint responds
    Given the API application
    When a client requests "/healthz"
    Then the response status is 200
    And the response body reports status "ok"

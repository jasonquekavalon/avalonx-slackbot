import requests


def add_mock_response(mock_server: str, path: str, status_code: int):
    """Adds an expectation to the mock server"""
    mock_server = "{}/expectation".format(mock_server)

    req_body = {
        "httpRequest": {
            "path": path
        },
        "httpResponse": {
            "statusCode": status_code
        }
    }

    req = requests.put(mock_server, data=str(req_body))
    if req.status_code != 201:
        raise requests.HTTPError("Mockserver returned non-201 status code when setting an expectation")


def add_mock_response_with_json(mock_server: str, path: str, status_code: int, response: str):
    """Adds an expectation to the mock server with a json response"""
    mock_server = "{}/expectation".format(mock_server)

    req_body = {
        "httpRequest": {
            "path": path
        },
        "httpResponse": {
            "headers": {
                "content-type": ["application/json"]
            },
            "statusCode": status_code,
            "body": {
                "type": "STRING",
                "string": response
            }
        }
    }

    req = requests.put(mock_server, data=str(req_body))
    if req.status_code != 201:
        raise requests.HTTPError("Mock server returned non-201 status code when setting an expectation")


def add_mock_response_matching_path_and_body(mock_server: str, path: str, status_code: int, body: dict):
    """Adds an expectation to the mock server that matches {path} and {body}"""
    mock_server = "{}/expectation".format(mock_server)

    req_body = {
        "httpRequest": {
            "path": path,
            "body": {
                "type": "JSON",
                "json": str(body)
            }
        },
        "httpResponse": {
            "statusCode": status_code,
        }
    }

    req = requests.put(mock_server, data=str(req_body))
    if req.status_code != 201:
        raise requests.HTTPError("Mock server returned non-201 status code when setting an expectation")


def reset_mock_server_response(mock_server: str, path: str):
    """Resets a mock server expectation"""
    mock_server = "{}/clear".format(mock_server)

    req_body = {
        "path": path
    }

    req = requests.put(mock_server, data=str(req_body))
    if req.status_code != 200:
        raise requests.HTTPError("Mock server returned non-200 status code when setting an expectation")


def verify_min_max(mock_server: str, path: str, at_least: int, at_most: int, body: dict):
    """
    Verify mock server was called at least and at most N number of times. Note: -1 is infinite number of times
    Mock server verification returns 202 on success and 406 on failure
    """
    mock_server = "{}/mockserver/verify".format(mock_server)
    
    req_body = {
        "httpRequest": {
            "path": path
        },
        "times": {
            "atLeast": at_least,
            "atMost": at_most
        }
    }

    req = requests.put(mock_server, data=str(req_body))
    return req.status_code

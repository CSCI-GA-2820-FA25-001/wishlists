# NYU DevOps Project Wishlist
[![Build Status](https://github.com/CSCI-GA-2820-FA25-001/wishlists/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA25-001/wishlists/actions)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-FA25-001/wishlists/graph/badge.svg?token=ERU6QBWIAX)](https://codecov.io/gh/CSCI-GA-2820-FA25-001/wishlists)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

A RESTful microservice for managing Wishlists and Wishlist Items, developed by the Wishlists Squad for NYU CSCI-GA-2820-FA25-001 DevOps and Agile Methodologies. 

## Overview

The Wishlist Service implements a REST API that allows clients to: 
- Create, Read, Update, Delete, and List wishlists
- Add and remove items from a wishlist
- Retrieve a specific wishlist item
- Filter wishlists by **category** (`?category=gifts`)
- Filter wishlists by **name** (`?name=holiday`)
- Reorder items inside a wishlist using `PATCH /wishlists/<id>/items <product_id>`

The `/service` folder contains your `models.py` file for your model and a `routes.py` file for your service. The `/tests` folder has test case starter code for testing the model and the service separately.

This project follows Test-Driven Development(TDD) practices and includes complete model and route tests with at lease 95% code coverage.

### JSON-only Responses
All API endpoints in this service return **JSON-formatted responses**, including error messages (e.g., 400, 404, 415, 500).  
This behavior is implemented through custom error handlers in `service/common/error_handlers.py`.


## Setup

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- VSCode Dev Containers (recommended)

### Installation

Clone the repository and open it in VSCode: 
```bash
    git clone <your_repo_url>
    cd <your_repo_name>
```
### Note
If you are using VSCode Remote Containers, open the folder and click "Reopen in Container". 

### Run the Service
```bash
    honcho start
```
Once running, open your browser and visit:
http://localhost:8080/

## Testing Instructions

### Run all tests:
```bash
    make test
```

### Run linter for PEP8 style
```bash
    make lint
```

All tests are located in the /tests folder:
- test_models.py - tests the data model
- test_routes.py - tests the REST API routes
- factories.py - creates fake data for testing

## REST API Endpoints

### Wishlists
| **Method** | **Endpoint** | **Description** | **Response** |
|---------------------|----------------------|-----------------------------|----------------------|
| `GET` | `/wishlists` | List all wishlists | `200 OK` |
| `POST` | `/wishlists` | Create a new wishlist | `201 Created`|
| `GET` | `/wishlists/<id>` | Retrieve a specific wishlist| `200 OK`|
| `PUT` | `/wishlists/<id>` | Update an existing wishlist | `200 OK` |
| `DELETE` | `/wishlists/<id>` | Delete a wishlist | `204 No Content`|

#### Query Parameters for `/wishlists`
- `category=<value>` — Filter by **category** (exact match, case-insensitive)  
- `name=<value>` — Filter by **name** (fuzzy match, case-insensitive)  

If neither query parameter is provided, the endpoint returns **all wishlists** for the current user.


### Wishlist Items
| **Method** | **Endpoint** | **Description** | **Response** |
|---------------------|----------------------|---------------------------|----------------------|
| `GET` | `/wishlists/<id>/items/<product_id>` | Retrieve a wishlist item | `200 OK`|
| `POST` | `/wishlists/<id>/items` | Add a new item to a wishlist | `201 Created`|
| `PUT` | `/wishlists/<id>/items/<product_id>`| Update an existing wishlist item | `200 OK` |
| `DELETE` | `/wishlists/<id>/items/<product_id>` | Delete an item | `204 No Content`|
| `PATCH` | `/wishlists/<id>/items/<product_id>` | Reorder a wishlist item (move before another item) | `200 OK` |

## Wishlist Examples

```json
{
    "customer_id": 1,
    "name": "Holiday Gifts 2025",
    "description": "Christmas presents for family and friends",
    "category": "gifts",
    "created_date": "2025-10-12"
}

{
    "customer_id": 1,
    "name": "Japan Trip Essentials",
    "description": "Things to buy before my Tokyo vacation",
    "category": "travel",
    "created_date": "2025-10-12"
}

{
    "customer_id": 1,
    "name": "Tech Upgrades",
    "description": "Electronics I want to purchase this year",
    "category": "electronics",
    "created_date": "2025-10-12"
}
```

### Wishlist Item Examples
```json
{
    "product_id": 101,
    "description": "Apple AirPods Pro",
    "position": 1
}

{
    "product_id": 202,
    "description": "Nintendo Switch OLED",
    "position": 2
}

{
    "product_id": 303,
    "description": "Sony WH-1000XM5 Headphones",
    "position": 3
}
```

## HTTP Status Codes

| **Code** | **Meaning** | **When It’s Used** |
|-----------|-------------|--------------------|
| `200 OK` | The request has succeeded | Returned for successful `GET` and `PUT` requests |
| `201 Created` | A new resource has been successfully created | Returned when a new wishlist or wishlist item is created |
| `204 No Content` | The request succeeded but returns no body | Returned when a wishlist or item is successfully deleted |
| `400 Bad Request` | The request was invalid or malformed | Returned when JSON is invalid or required fields are missing |
| `403 Forbidden` | The request is understood but refused | Returned when trying to update another user’s wishlist |
| `404 Not Found` | The requested resource does not exist | Returned when a wishlist or item cannot be found |
| `405 Method Not Allowed` | The method is not supported for the endpoint | Returned when using an unsupported HTTP method (e.g., `PUT` on `/wishlists`) |
| `409 Conflict` | A resource conflict occurred | Returned when a request causes a business logic conflict |
| `415 Unsupported Media Type` | The request has an unsupported Content-Type | Returned when the `Content-Type` is not `application/json` |
| `500 Internal Server Error` | The server encountered an unexpected error | Returned when an unhandled exception occurs on the server |


## Contents

The project contains the following:

```text
.gitignore          - this will ignore vagrant and other metadata files
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to gix Windows CRLF issues
.devcontainers/     - Folder with support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
pyproject.toml      - Poetry list of Python libraries required by your code

service/                   - service python package
├── __init__.py            - package initializer
├── config.py              - configuration parameters
├── models.py              - module with business models
├── routes.py              - module with service routes
└── common                 - common code package
    ├── cli_commands.py    - Flask command to recreate all tables
    ├── error_handlers.py  - HTTP error handling code
    ├── log_handlers.py    - logging setup code
    └── status.py          - HTTP status constants

tests/                     - test cases package
├── __init__.py            - package initializer
├── factories.py           - Factory for testing with fake objects
├── test_cli_commands.py   - test suite for the CLI
├── test_models.py         - test suite for business models
└── test_routes.py         - test suite for service routes
```

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.

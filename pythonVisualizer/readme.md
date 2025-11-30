# Camel Route Visualizer

A Flask-based Python application that visualizes Apache Camel routes by querying JMX data through Jolokia.

## Overview

This application provides a REST API to inspect Camel routes running in your application. It uses Jolokia (JMX over HTTP) to retrieve real-time information about routes, their statistics, and configuration.

## Prerequisites

- Python 3.12+
- Running Camel application with Jolokia enabled (dev profile)
- The Loco Camel application running on port 8080

## Installation

1. Create and activate virtual environment (if not already created):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Using the run script
```bash
./run.sh
```

### Option 2: Manual execution
```bash
source .venv/bin/activate
python app.py
```

The Flask application will start on http://localhost:5000

## Available Endpoints

### 1. Home Page
**GET** `/`

Returns an HTML page with API documentation and links to test endpoints.

**Example:**
```bash
curl http://localhost:5000/
```

### 2. List All Routes
**GET** `/routes`

Gets a list of all Camel routes in the system by ID.

**Example:**
```bash
curl http://localhost:5000/routes
```

**Response:**
```json
{
  "count": 1,
  "routes": [
    "hello-route"
  ]
}
```

### 3. Get Route Details
**GET** `/route/<route_id>`

Gets detailed information about a specific route including statistics, configuration, and state.

**Example:**
```bash
curl http://localhost:5000/route/hello-route
```

**Response:**
```json
{
  "routeId": "hello-route",
  "mbean": "org.apache.camel:context=camel-1,name=\"hello-route\",type=routes",
  "state": "Started",
  "uptime": "5m30s",
  "camelId": "camel-1",
  "description": null,
  "endpointUri": "direct://hello",
  "statistics": {
    "exchangesTotal": 5,
    "exchangesCompleted": 5,
    "exchangesFailed": 0,
    "failuresHandled": 0,
    "redeliveries": 0,
    "externalRedeliveries": 0,
    "minProcessingTime": 0,
    "maxProcessingTime": 5,
    "meanProcessingTime": 1,
    "totalProcessingTime": 6,
    "lastProcessingTime": 0,
    "deltaProcessingTime": 0
  },
  "properties": {
    "customId": "true",
    "description": null,
    "id": "hello-route",
    "kamelet": "false",
    "parent": "2a16d393",
    "rest": "false",
    "template": "false"
  },
  "hasCustomIdAssigned": null,
  "supportsRestart": null,
  "routeDefinition": null
}
```

## Architecture

```
┌─────────────────────┐      HTTP/REST      ┌─────────────────────┐
│  Python Visualizer  │ ◄─────────────────► │  Jolokia Endpoint   │
│  (Flask on :5000)   │   JSON Requests     │  (:8080/actuator/   │
└─────────────────────┘                     │      jolokia)       │
                                            └─────────────────────┘
                                                      ▲
                                                      │ JMX
                                                      │
                                            ┌─────────────────────┐
                                            │  Apache Camel       │
                                            │  Routes & MBeans    │
                                            └─────────────────────┘
```

## How It Works

1. **Jolokia Integration**: The Flask app communicates with Jolokia, which exposes JMX MBeans over a REST+JSON API
2. **Route Discovery**: Uses Jolokia's search operation to find all Camel route MBeans matching the pattern `org.apache.camel:type=routes,*`
3. **Data Retrieval**: Reads MBean attributes to get route state, statistics, and configuration
4. **Real-time Statistics**: Every request fetches fresh data from the running Camel application

## Testing

First, ensure your Camel application is running:
```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn spring-boot:run
```

Then start the Python visualizer:
```bash
./run.sh
```

Test the endpoints:
```bash
# List all routes
curl http://localhost:5000/routes

# Get route details
curl http://localhost:5000/route/hello-route

# Trigger the route to see statistics update
curl http://localhost:8080/camel

# Check updated statistics
curl http://localhost:5000/route/hello-route
```

## Files

- `app.py` - Main Flask application with all endpoints
- `requirements.txt` - Python dependencies (Flask, requests)
- `run.sh` - Convenience script to run the application
- `readme.md` - This file

## Future Enhancements

Potential additions to this visualizer:
- HTML/JavaScript frontend for interactive route visualization
- Route diagram rendering (similar to Hawtio)
- Real-time WebSocket updates for statistics
- Route control operations (start/stop/suspend)
- Message browsing and inspection
- Performance charts and graphs
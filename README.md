# Loco Camel

A Spring Boot application demonstrating Apache Camel integration with web-based debugging capabilities using Hawtio.

## Disclaimer

I have used AI to generate most of this project :) It still took a while.

## Technologies

- **Java 21**
- **Spring Boot 3.2.0**
- **Apache Camel 4.14.0**
- **Maven**
- **Log4j2** (configured with fully qualified class names, line numbers, and timestamps)
- **Hawtio 4.2.0** (web-based Camel debugging console)

## Prerequisites

- Java 21 (OpenJDK 21)
- Maven 3.x
- A web browser (for Hawtio debugging interface)

## Project Structure

```
locoCamel/
├── src/
│   └── main/
│       ├── java/org/moriano/lococamel/
│       │   ├── LocoCamelApplication.java     # Main Spring Boot application
│       │   ├── controller/
│       │   │   └── ApiController.java        # REST endpoints
│       │   └── route/
│       │       └── HelloRoute.java           # Camel route definition
│       └── resources/
│           ├── application.properties        # Application configuration
│           └── log4j2.xml                   # Log4j2 configuration
├── pom.xml                                   # Maven dependencies
└── README.md
```

## Building the Project

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn clean package
```

## Running the Application

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn spring-boot:run
```

The application will start on port **8080**.

## Available Endpoints

### REST Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/ping` | GET | Health check endpoint | `"pong"` |
| `/camel` | GET | Triggers Camel route execution | `"Hello from Apache Camel!"` |

### Management Endpoints

| Endpoint | Description |
|----------|-------------|
| `/actuator/hawtio` | Hawtio web console for debugging |

## The Camel Route

The project includes a simple Camel route (`hello-route`) defined in `HelloRoute.java`:

```java
from("direct:hello")
    .routeId("hello-route")
    .log("Received request to hello route").id("log-start")
    .setBody(constant("Hello from Apache Camel!")).id("set-body")
    .log("Returning response: ${body}").id("log-end");
```

``This route:
1. Receives messages from the `direct:hello` endpoint
2. Logs the incoming request
3. Sets the message body to "Hello from Apache Camel!"
4. Logs the response
5. Returns the message
``
Each step has an explicit ID (`log-start`, `set-body`, `log-end`) which is required for debugging.

## Debugging with Hawtio

Hawtio provides a powerful web-based interface for debugging and monitoring Apache Camel routes in real-time.

### Step 1: Start the Application

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn spring-boot:run
```

Wait for the application to fully start. You should see:
```
Started LocoCamelApplication in X.XXX seconds
```

### Step 2: Access Hawtio Console

Open your web browser and navigate to:

```
http://localhost:8080/actuator/hawtio
```

You'll see the Hawtio dashboard (no authentication required in this configuration).

### Step 3: Navigate to Camel Routes

1. In the left sidebar, click on **"Camel"**
2. You'll see your Camel context named `camel-1`
3. Click on **"Routes"** to see all available routes
4. Click on **`hello-route`** to view the route details

### Step 4: View Route Diagram

The Hawtio console will display a visual diagram of your route showing:
- All EIP (Enterprise Integration Pattern) steps
- The flow from `direct:hello` through each step
- Each node labeled with its ID (`log-start`, `set-body`, `log-end`)

### Step 5: Enable Route Debugging

1. In the route view, click on the **"Debug"** tab
2. Click the **"Start Debugging"** button
3. The route is now in debug mode

### Step 6: Set Breakpoints

1. Click on any step in the route diagram (e.g., `log-start` or `set-body`)
2. In the context menu or details panel, click **"Add Breakpoint"** or **"Toggle Breakpoint"**
3. A breakpoint indicator (usually a red dot) will appear on that step

### Step 7: Trigger the Route

Execute a request to trigger the route:

```bash
curl http://localhost:8080/camel
```

### Step 8: Debug the Message

When the route hits a breakpoint:
1. The execution will **pause** at that step
2. In Hawtio, you'll see the **suspended message** highlighted
3. You can inspect:
   - **Message Body** - the current content of the message
   - **Message Headers** - all Camel headers
   - **Exchange Properties** - exchange-level properties
   - **Stack Trace** - the execution path

### Step 9: Step Through the Route

Use the debugging controls:
- **Step Over** - Execute the current step and move to the next one
- **Resume** - Continue execution until the next breakpoint
- **Stop** - Terminate the message exchange

### Step 10: Inspect and Modify

While debugging, you can:
- View the complete message exchange details
- Inspect header values
- See the body content at each step
- Monitor route statistics and performance metrics

### Additional Hawtio Features

#### Route Metrics
- Click on the **"Attributes"** or **"Chart"** tab to see:
  - Number of messages processed
  - Processing time (min/max/average)
  - Failure rate
  - Throughput

#### Message Tracing
- Enable **"Tracing"** to see the complete flow of messages
- View timing information for each step
- Identify performance bottlenecks

#### Route Control
- **Start/Stop** routes dynamically
- **Suspend/Resume** routes
- View route status and statistics

## Configuration Details

### Debug Configuration

The following properties in `application.properties` enable Camel debugging:

```properties
# Enable JMX for monitoring
camel.springboot.jmx-enabled=true

# Enable Camel debugging
camel.debug.enabled=true

# Enable message tracing
camel.springboot.backlog-tracing=true

# Start debugger in standby mode (waits for connection)
camel.debug.standby=true

# Enable JMX connector for remote debugging
camel.debug.jmx-connector-enabled=true
camel.debug.jmx-connector-port=1099

# Hawtio configuration
management.endpoints.web.exposure.include=hawtio,jolokia
hawtio.authenticationEnabled=false
```

### Log Configuration

Logs are configured in `log4j2.xml` to display:
- Timestamp (yyyy-MM-dd HH:mm:ss.SSS)
- Thread name
- Log level
- **Fully qualified class name**
- **Line number**
- Log message

Example log output:
```
2025-11-15 17:04:53.464 [main] INFO  org.moriano.lococamel.LocoCamelApplication:50 - Starting LocoCamelApplication
```

## IntelliJ IDEA Setup

If you're using IntelliJ IDEA, configure it to use Java 21:

### Project SDK
1. **File → Project Structure → Project**
2. SDK: Java 21 (java-1.21.0-openjdk-amd64)
3. Language Level: 21

### Maven Runner
1. **File → Settings → Build, Execution, Deployment → Build Tools → Maven → Runner**
2. JRE: Java 21
3. Or add environment variable: `JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64`

## Testing the Application

### Test the ping endpoint
```bash
curl http://localhost:8080/ping
```
Expected response: `pong`

### Test the Camel route
```bash
curl http://localhost:8080/camel
```
Expected response: `Hello from Apache Camel!`

### View logs
Check the console output to see:
```
2025-11-15 17:04:54.XXX [http-nio-8080-exec-1] INFO  org.moriano.lococamel.route.HelloRoute:13 - Received request to hello route
2025-11-15 17:04:54.XXX [http-nio-8080-exec-1] INFO  org.moriano.lococamel.route.HelloRoute:15 - Returning response: Hello from Apache Camel!
```

## Troubleshooting

### Port 8080 already in use
If you see an error about port 8080 being in use, either:
- Stop the process using port 8080
- Change the port in `application.properties`: `server.port=8081`

### Java version mismatch
If you get "release version 21 not supported":
- Ensure Java 21 is installed: `java -version`
- Set JAVA_HOME correctly: `JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64`

### Hawtio not accessible
If you can't access http://localhost:8080/actuator/hawtio:
- Verify the application started successfully
- Check that `hawtio-springboot` dependency is in `pom.xml`
- Verify `management.endpoints.web.exposure.include=hawtio,jolokia` is set

## Why Hawtio Instead of IDE Plugins?

While IntelliJ IDEA has an Apache Camel plugin, **Hawtio offers several advantages**:

1. **Works with Community Edition** - No need for IntelliJ Ultimate
2. **Browser-based** - Debug from anywhere, no IDE required
3. **Visual route diagrams** - Better visualization of complex routes
4. **Real-time monitoring** - Live metrics and performance data
5. **Production-ready** - Can be used in non-development environments
6. **No version compatibility issues** - Works consistently across IDE versions

## Next Steps

To extend this project, you could:
- Add more complex Camel routes with processors and transformations
- Integrate with external systems (databases, message queues, REST APIs)
- Add error handling and retry logic
- Implement route testing with Camel Test Kit
- Add Spring Boot Actuator health checks for Camel routes
- Secure the Hawtio console with authentication

## License

This is a demonstration project for learning Apache Camel debugging techniques.

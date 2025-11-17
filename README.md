# Loco Camel

A Spring Boot application demonstrating Apache Camel integration with web-based debugging capabilities using Hawtio.

## Disclaimer

I have used AI to generate most of this project :) It still took a while.

## Quick Reference

### Development (with debugging via standalone Hawtio)
```bash
# Terminal 1: Start your Camel application
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn spring-boot:run

# Terminal 2: Install JBang (first time only)
curl -Ls https://sh.jbang.dev | bash -s - app setup
export PATH="$HOME/.jbang/bin:$PATH"

# Install Hawtio via JBang (first time only)
jbang app install hawtio@hawtio/hawtio

# Run Hawtio and connect to your application
hawtio --connection http://localhost:8080/actuator/jolokia --port 9090

# Access Hawtio console (automatically connected)
http://localhost:9090/hawtio
```

### Production (no debugging tools)
```bash
# Build
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn clean package -Pprod

# Run
java -Dspring.profiles.active=prod -jar target/loco-camel-1.0-SNAPSHOT.jar
```

## Technologies

- **Java 21**
- **Spring Boot 3.2.0**
- **Apache Camel 4.14.0**
- **Maven**
- **Log4j2** (configured with fully qualified class names, line numbers, and timestamps)
- **Jolokia** (JMX over HTTP bridge for remote debugging)
- **Hawtio 4.6.1** (standalone web-based Camel debugging console via JBang)
- **JBang** (Java scripting tool for running standalone Hawtio)

## Prerequisites

- Java 21 (OpenJDK 21)
- Maven 3.x
- A web browser (for Hawtio debugging interface)
- JBang (optional, for running standalone Hawtio - auto-installed via curl command)

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
│           ├── application.properties        # Common configuration
│           ├── application-dev.properties    # Development-specific config
│           ├── application-prod.properties   # Production-specific config
│           └── log4j2.xml                   # Log4j2 configuration
├── pom.xml                                   # Maven dependencies with profiles
├── run-hawtio.sh                            # Standalone Hawtio launcher (Linux/Mac)
├── run-hawtio.bat                           # Standalone Hawtio launcher (Windows)
└── README.md
```

## Profiles: Development vs Production

This project uses **Maven profiles** and **Spring profiles** to separate development and production configurations:

### Maven Profiles (Dependencies)

- **`dev` profile** (active by default):
  - Includes `camel-debug` for route debugging
  - Includes `jolokia-core` for JMX over HTTP (allows Hawtio to connect remotely)
  - Enables JMX monitoring on port 1099
  - Suitable for local development with standalone Hawtio

- **`prod` profile**:
  - Excludes all debugging dependencies (camel-debug, jolokia)
  - Smaller, more secure artifact
  - No JMX or debug overhead
  - Suitable for production deployments

### Spring Profiles (Configuration)

- **`dev` profile** (`application-dev.properties`):
  - Enables Camel debugging (`camel.debug.enabled=true`)
  - Enables JMX (`camel.springboot.jmx-enabled=true`)
  - Exposes Jolokia endpoint at `/actuator/jolokia` for Hawtio connection
  - Enables message backlog tracing
  - JMX connector on port 1099

- **`prod` profile** (`application-prod.properties`):
  - Disables all debugging features
  - Disables JMX
  - Does not expose Jolokia endpoint
  - Only exposes health and info endpoints
  - Security-focused configuration

## Building the Project

### For Development (with debugging tools)

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn clean package -Pdev
```

Or simply (dev is the default profile):

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn clean package
```

### For Production (without debugging tools)

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn clean package -Pprod
```

This will create a **smaller JAR file** without Hawtio, camel-debug, and JMX dependencies.

## Running the Application

### Development Mode (with Hawtio and debugging)

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn spring-boot:run -Pdev
```

Or set the Spring profile via command line:

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

Or run the built JAR:

```bash
java -Dspring.profiles.active=dev -jar target/loco-camel-1.0-SNAPSHOT.jar
```

### Production Mode (without debugging)

Build with production profile and run:

```bash
# Build for production
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn clean package -Pprod

# Run with production profile
java -Dspring.profiles.active=prod -jar target/loco-camel-1.0-SNAPSHOT.jar
```

Or via Maven:

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn spring-boot:run -Pprod -Dspring-boot.run.profiles=prod
```

The application will start on port **8080**.

### Environment Variable Method

You can also set the active profile via environment variable:

```bash
export SPRING_PROFILES_ACTIVE=prod
java -jar target/loco-camel-1.0-SNAPSHOT.jar
```

## Available Endpoints

### REST Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/ping` | GET | Health check endpoint | `"pong"` |
| `/camel` | GET | Triggers Camel route execution | `"Hello from Apache Camel!"` |

### Management Endpoints

| Endpoint | Description | Availability |
|----------|-------------|--------------|
| `/actuator/jolokia` | Jolokia JMX over HTTP endpoint (for Hawtio connection) | **Dev profile only** |
| `/actuator/health` | Application health status | All profiles |
| `/actuator/info` | Application information | All profiles |

**Note**:
- The Jolokia endpoint is only available when running with the `dev` profile
- Hawtio runs as a **separate standalone server** on port 8090 and connects to your application via the Jolokia endpoint
- In production, Jolokia is disabled for security

## The Camel Route

The project includes a simple Camel route (`hello-route`) defined in `HelloRoute.java`:

```java
from("direct:hello")
    .routeId("hello-route")
    .log("Received request to hello route")
    .setBody(constant("Hello from Apache Camel!"))
    .log("Returning response: ${body}");
```

``This route:
1. Receives messages from the `direct:hello` endpoint
2. Logs the incoming request
3. Sets the message body to "Hello from Apache Camel!"
4. Logs the response
5. Returns the message
``

## Debugging with Hawtio

Hawtio runs as a **standalone server** that connects to your Camel application via Jolokia (JMX over HTTP). This provides a powerful web-based interface for debugging and monitoring Apache Camel routes in real-time. The modern approach uses **JBang** to run the latest Hawtio 4.6.1.

### Architecture Overview

```
┌──────────────────────┐         Jolokia/JMX          ┌──────────────────────┐
│  Hawtio Server       │  ◄─────────────────────────► │  Camel Application   │
│  (port 9090)         │      HTTP Connection         │  (port 8080)         │
│  JBang + Hawtio 4.6.1│                              │  Your app + Routes   │
└──────────────────────┘                              └──────────────────────┘
```

### Step 1: Start the Camel Application

Open a terminal and start your Camel application with the dev profile:

```bash
JAVA_HOME=/usr/lib/jvm/java-1.21.0-openjdk-amd64 mvn spring-boot:run
```

Wait for the application to fully start. You should see:
```
Started LocoCamelApplication in X.XXX seconds
The following profiles are active: dev
```

Verify the Jolokia endpoint is available:
```bash
curl http://localhost:8080/actuator/jolokia
```

You should see a JSON response with version information.

### Step 2: Install JBang (First Time Only)

Open a **second terminal** and install JBang:

```bash
curl -Ls https://sh.jbang.dev | bash -s - app setup
export PATH="$HOME/.jbang/bin:$PATH"
```

### Step 3: Install Hawtio via JBang (First Time Only)

```bash
jbang app install hawtio@hawtio/hawtio
```

This will download and install Hawtio 4.6.1 (the latest version from November 2025).

### Step 4: Start Hawtio and Connect to Your Application

```bash
hawtio --connection http://localhost:8080/actuator/jolokia --port 9090
```

The `--connection` flag automatically connects Hawtio to your Camel application via Jolokia, so you don't need to manually configure the connection in the UI!

### Step 5: Access Hawtio Console

Open your web browser and navigate to:

```
http://localhost:9090/hawtio
```

You'll see the Hawtio dashboard **already connected** to your Camel application!

### Step 6: Navigate to Camel Routes

Once connected:

1. In the left sidebar, click on **"Camel"**
2. You'll see your Camel context named `camel-1`
3. Click on **"Routes"** to see all available routes
4. Click on **`hello-route`** to view the route details

### Step 7: View Route Diagram

The Hawtio console will display a visual diagram of your route showing:
- All EIP (Enterprise Integration Pattern) steps
- The flow from `direct:hello` through each step

### Step 8: Enable Route Debugging

1. In the route view, click on the **"Debug"** tab
2. Click the **"Start Debugging"** button
3. The route is now in debug mode

### Step 9: Set Breakpoints

1. Click on any step in the route diagram
2. In the context menu or details panel, click **"Add Breakpoint"** or **"Toggle Breakpoint"**
3. A breakpoint indicator (usually a red dot) will appear on that step

### Step 10: Trigger the Route

Execute a request to trigger the route:

```bash
curl http://localhost:8080/camel
```

### Step 11: Debug the Message

When the route hits a breakpoint:
1. The execution will **pause** at that step
2. In Hawtio, you'll see the **suspended message** highlighted
3. You can inspect:
   - **Message Body** - the current content of the message
   - **Message Headers** - all Camel headers
   - **Exchange Properties** - exchange-level properties
   - **Stack Trace** - the execution path

### Step 12: Step Through the Route

Use the debugging controls:
- **Step Over** - Execute the current step and move to the next one
- **Resume** - Continue execution until the next breakpoint
- **Stop** - Terminate the message exchange

### Step 13: Inspect and Modify

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

### Profile-Based Configuration

Configuration is now split across three files:

1. **`application.properties`**: Common configuration for all environments
   ```properties
   server.port=8080
   spring.application.name=loco-camel
   spring.profiles.active=dev  # Default profile
   ```

2. **`application-dev.properties`**: Development-specific configuration
   ```properties
   # Enable JMX for monitoring
   camel.springboot.jmx-enabled=true
   spring.jmx.enabled=true

   # Enable Camel debugging
   camel.debug.enabled=true

   # Enable message tracing
   camel.springboot.backlog-tracing=true

   # Start debugger in standby mode
   camel.debug.standby=true

   # Enable JMX connector for remote debugging
   camel.debug.jmx-connector-enabled=true
   camel.debug.jmx-connector-port=1099

   # Jolokia configuration (for Hawtio connection via HTTP)
   management.endpoints.web.exposure.include=jolokia,health,info
   management.endpoint.jolokia.enabled=true
   management.endpoint.jolokia.config.debug=true
   ```

3. **`application-prod.properties`**: Production-specific configuration
   ```properties
   # Disable all debugging features
   camel.springboot.jmx-enabled=false
   camel.debug.enabled=false
   camel.springboot.backlog-tracing=false

   # Only expose essential endpoints
   management.endpoints.web.exposure.include=health,info
   ```

### Verifying Profile Configuration

To verify which profile is active, check the startup logs:

```
The following profiles are active: dev
```

Or check the artifact size difference:

```bash
# Build both profiles
mvn clean package -Pdev
ls -lh target/loco-camel-1.0-SNAPSHOT.jar

mvn clean package -Pprod
ls -lh target/loco-camel-1.0-SNAPSHOT.jar
```

The production build will be several megabytes smaller due to excluded debugging dependencies.

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
If you can't access http://localhost:9090/hawtio:
- **Verify you started Hawtio via JBang** using `hawtio --connection http://localhost:8080/actuator/jolokia --port 9090`
- Check that port 9090 is not in use by another application: `lsof -i :9090` (Linux/Mac) or `netstat -ano | findstr :9090` (Windows)
- Verify JBang is installed: `jbang version`
- Check if the PATH includes JBang: `echo $PATH | grep jbang`

### Cannot connect Hawtio to Camel application
If Hawtio cannot connect to your application (when using `--connection` flag, this should be automatic):
- **Verify you're running the Camel app with the dev profile** (not prod)
- Check the startup logs for: `The following profiles are active: dev`
- Ensure you built with `-Pdev` Maven profile
- Test the Jolokia endpoint manually:
  ```bash
  curl http://localhost:8080/actuator/jolokia
  ```
- Verify Jolokia is exposed in the management endpoints
- Check that both applications are running (Camel app on 8080, Hawtio on 9090)
- If using the `--connection` flag with JBang, ensure the URL is correct: `http://localhost:8080/actuator/jolokia`

### Profile-related issues

**Problem**: Jolokia endpoint returns 404
- **Solution**: Ensure you're running with the dev profile and rebuild: `mvn clean package -Pdev`

**Problem**: Want to change default profile from dev to prod
- **Solution**: Edit `application.properties` and change `spring.profiles.active=dev` to `spring.profiles.active=prod`

**Problem**: Running in production but debugging features still enabled
- **Solution**: Ensure both Maven profile AND Spring profile are set to prod:
  ```bash
  mvn clean package -Pprod
  java -Dspring.profiles.active=prod -jar target/loco-camel-1.0-SNAPSHOT.jar
  ```

**Problem**: Want to verify no debug dependencies in production JAR
- **Solution**: Inspect the JAR contents:
  ```bash
  jar -tf target/loco-camel-1.0-SNAPSHOT.jar | grep -i jolokia
  jar -tf target/loco-camel-1.0-SNAPSHOT.jar | grep -i camel-debug
  ```
  Should return empty for production build.

**Problem**: JBang installation fails
- **Solution**: Try manual JBang installation:
  - Download from https://www.jbang.dev/download/
  - Or use package managers: `brew install jbangdev/tap/jbang` (Mac), `scoop install jbang` (Windows)
  - Verify installation: `jbang version`

**Problem**: Hawtio installation via JBang fails
- **Solution**:
  - Ensure JBang is in PATH: `export PATH="$HOME/.jbang/bin:$PATH"`
  - Clear JBang cache: `jbang cache clear`
  - Reinstall: `jbang app install hawtio@hawtio/hawtio --force`

## Why Use Profiles?

### Benefits of Separating Dev and Production Configurations

1. **Smaller Production Artifacts**
   - Production JARs exclude debugging dependencies (camel-debug)
   - Dev JAR: ~40 MB, Prod JAR: ~35 MB (5 MB difference)
   - No embedded Hawtio means even dev profile stays lean
   - Faster deployments and reduced storage costs
   - Smaller attack surface

2. **Enhanced Security**
   - No JMX ports exposed in production
   - No Hawtio web console in production
   - Reduced risk of information disclosure

3. **Better Performance**
   - No debugging overhead in production
   - No message tracing or backlog collection
   - Lower memory footprint

4. **Simplified Development**
   - Full debugging capabilities locally
   - No need to modify code to enable/disable debugging
   - Easy switching between environments

5. **Best Practices Compliance**
   - Follows Spring Boot recommended patterns
   - Clear separation of concerns
   - Environment-specific configuration

### Key Differences Between Profiles

| Feature | Dev Profile | Prod Profile |
|---------|-------------|--------------|
| **JAR Size** | ~40 MB | ~35 MB |
| **Hawtio Console** | Standalone via JBang (port 9090) | Not available |
| **Jolokia (JMX over HTTP)** | Enabled (~200 KB) | Not included |
| **Camel Debug** | Enabled | Not included |
| **JMX** | Enabled (port 1099) | Disabled |
| **Message Tracing** | Enabled | Disabled |
| **Exposed Endpoints** | jolokia, health, info | health, info only |
| **Security** | Development-friendly | Production-hardened |
| **Architecture** | 2 processes (app + Hawtio via JBang) | 1 process (app only) |
| **Hawtio Version** | 4.6.1 (November 2025, external) | N/A |
| **Hawtio Embedded in JAR** | No (~10 MB savings) | No |

## Why Standalone Hawtio via JBang?

### Benefits of Running Hawtio as a Separate Process with JBang

1. **Complete Separation of Concerns**
   - Your application JAR contains zero debugging/monitoring code
   - Even in dev profile, the app remains lean
   - Hawtio can be stopped/started independently

2. **Always Up-to-Date**
   - JBang fetches the latest Hawtio version (4.6.1 from November 2025)
   - No need to manually download JAR files or track updates
   - Easy to upgrade: just reinstall via JBang

3. **One Hawtio, Multiple Applications**
   - Connect a single Hawtio instance to multiple Camel applications
   - Monitor and debug multiple microservices from one dashboard
   - Useful in distributed systems development

4. **Zero Production Risk**
   - Impossible to accidentally deploy Hawtio to production
   - No web console embedded in your application
   - Jolokia endpoint is still profile-controlled for security

5. **Flexible Deployment**
   - Run Hawtio on a different machine and connect remotely
   - Easy to share debugging sessions with team members
   - Can run Hawtio in Docker while app runs locally

6. **Smaller Artifacts**
   - No embedded Hawtio in your JAR (~10 MB savings compared to embedded approach)
   - Only need Jolokia for remote JMX access (~200 KB)
   - Faster build times and smaller deployments
   - Even the dev profile JAR is lean (~40 MB vs ~50 MB with embedded Hawtio)

7. **Automatic Connection**
   - Using `--connection` flag eliminates manual connection setup
   - Hawtio opens already connected to your application
   - No need to configure Jolokia URL in the UI

## Why Hawtio Instead of IDE Plugins?

While IntelliJ IDEA has an Apache Camel plugin, **Hawtio offers several advantages**:

1. **Works with Community Edition** - No need for IntelliJ Ultimate
2. **Browser-based** - Debug from anywhere, no IDE required
3. **Visual route diagrams** - Better visualization of complex routes
4. **Real-time monitoring** - Live metrics and performance data
5. **Can connect to running applications** - Even in remote environments (with proper security)
6. **No version compatibility issues** - Works consistently across IDE versions
7. **Team collaboration** - Share Hawtio URL for collaborative debugging

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

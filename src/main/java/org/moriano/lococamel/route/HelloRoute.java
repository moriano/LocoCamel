package org.moriano.lococamel.route;

import org.apache.camel.builder.RouteBuilder;
import org.springframework.stereotype.Component;

@Component
public class HelloRoute extends RouteBuilder {

    @Override
    public void configure() throws Exception {
        from("direct:hello")
            .routeId("hello-route")
            .log("Received request to hello route")
            .setBody(constant("Hello from Apache Camel!"))
            .log("Returning response: ${body}");
    }
}

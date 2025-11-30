package org.moriano.lococamel.route;

import org.apache.camel.builder.RouteBuilder;
import org.springframework.stereotype.Component;

@Component
public class GoodbyeRoute extends RouteBuilder {

    @Override
    public void configure() throws Exception {
        from("direct:goodbye")
            .routeId("goodbye-route")
            .log("Received request to goodbye route")
            .setBody(constant("Goodbye from Apache Camel!"))
            .log("Returning response: ${body}");
    }
}

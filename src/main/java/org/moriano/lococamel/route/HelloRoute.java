package org.moriano.lococamel.route;

import org.apache.camel.builder.RouteBuilder;
import org.springframework.stereotype.Component;

@Component
public class HelloRoute extends RouteBuilder {

    @Override
    public void configure() throws Exception {
        from("direct:hello")
            .routeId("hello-route")
            .log("Received request to hello route").id("log-start")
            .setBody(constant("Hello from Apache Camel!")).id("set-body")
            .log("Returning response: ${body}").id("log-end");
    }
}

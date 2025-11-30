package org.moriano.lococamel.route;

import org.apache.camel.builder.RouteBuilder;
import org.springframework.stereotype.Component;

@Component
public class HelloAndGoodbyeRoute extends RouteBuilder {

    @Override
    public void configure() throws Exception {
        from("direct:hello-and-goodbye")
            .routeId("hello-and-goodbye-route")
            .log("This is a hello and goodbye route")
            .to("direct:hello")
            .log("Called hello route, result: ${body}")
            .to("direct:goodbye")
            .log("Called goodbye route, result: ${body}");
    }
}

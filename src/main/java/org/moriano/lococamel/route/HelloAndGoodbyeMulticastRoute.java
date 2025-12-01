package org.moriano.lococamel.route;

import org.apache.camel.builder.RouteBuilder;
import org.springframework.stereotype.Component;

@Component
public class HelloAndGoodbyeMulticastRoute extends RouteBuilder {

    @Override
    public void configure() throws Exception {
        from("direct:hello-and-goodbye-multicast")
            .routeId("hello-and-goodbye-multicast-route")
            .log("This is a hello and goodbye multicast route")
            .multicast()
                .to("direct:hello")
                .to("direct:goodbye")
            .end()
            .log("Finished multicast, result: ${body}");
    }
}

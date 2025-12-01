package org.moriano.lococamel.route;

import org.apache.camel.builder.RouteBuilder;
import org.springframework.stereotype.Component;

@Component
public class MegaRoute extends RouteBuilder {

    @Override
    public void configure() throws Exception {
        from("direct:mega")
            .routeId("mega-route")
            .log("This is the mega route")
            .multicast()
                .to("direct:hello")
                .to("direct:goodbye")
                .to("direct:choice")
            .end()
            .log("Finished mega route");
    }
}

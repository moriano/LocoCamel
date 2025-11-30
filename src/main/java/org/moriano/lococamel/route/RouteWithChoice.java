package org.moriano.lococamel.route;

import org.apache.camel.builder.RouteBuilder;
import org.springframework.stereotype.Component;

@Component
public class RouteWithChoice extends RouteBuilder {

    @Override
    public void configure() throws Exception {
        from("direct:choice")
            .routeId("choice-route")
            .log("Received request to choice route")
            .setProperty("currentMillis", method(this, "getCurrentMillis"))
            .log("Current milliseconds: ${exchangeProperty.currentMillis}")
            .choice()
                .when(exchange -> {
                    Integer millis = exchange.getProperty("currentMillis", Integer.class);
                    return millis != null && millis % 3 == 0;
                })
                    .log("Milliseconds divisible by 3 - returning Fizz")
                    .setBody(constant("Fizz"))
                .when(exchange -> {
                    Integer millis = exchange.getProperty("currentMillis", Integer.class);
                    return millis != null && millis % 5 == 0;
                })
                    .log("Milliseconds divisible by 5 - returning Buzz")
                    .setBody(constant("Buzz"))
                .otherwise()
                    .log("Milliseconds not divisible by 3 or 5 - returning Mumble")
                    .setBody(constant("Mumble"))
            .end()
            .log("Returning response: ${body}");
    }

    public Integer getCurrentMillis() {
        return (int) (System.currentTimeMillis() % 1000);
    }
}

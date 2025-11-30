package org.moriano.lococamel.controller;

import org.apache.camel.ProducerTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ApiController {

    @Autowired
    private ProducerTemplate producerTemplate;

    @GetMapping("/ping")
    public String ping() {
        return "pong";
    }

    @GetMapping("/camel")
    public String camel() {
        String result = producerTemplate.requestBody("direct:hello", null, String.class);
        return result;
    }

    @GetMapping("/choice")
    public String choice() {
        String result = producerTemplate.requestBody("direct:choice", null, String.class);
        return result;
    }

    @GetMapping("/goodbye")
    public String goodbye() {
        String result = producerTemplate.requestBody("direct:goodbye", null, String.class);
        return result;
    }

    @GetMapping("/hello-and-goodbye")
    public String helloAndGoodbye() {
        String result = producerTemplate.requestBody("direct:hello-and-goodbye", null, String.class);
        return result;
    }
}

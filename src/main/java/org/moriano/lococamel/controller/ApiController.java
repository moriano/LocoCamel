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
}

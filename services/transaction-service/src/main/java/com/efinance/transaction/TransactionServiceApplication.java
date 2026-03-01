package com.efinance.transaction;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * E-Finance Transaction Processing Service
 * High-performance transaction processing with Kafka integration
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
public class TransactionServiceApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(TransactionServiceApplication.class, args);
    }
}


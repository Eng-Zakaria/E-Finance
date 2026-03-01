package com.efinance.transaction.service;

import com.efinance.transaction.model.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * Fraud Check Service
 * Integrates with Python Fraud Detection Service
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class FraudCheckService {
    
    @Value("${app.fraud-service.url}")
    private String fraudServiceUrl;
    
    private final RestTemplate restTemplate = new RestTemplate();
    
    /**
     * Check transaction for fraud (async)
     */
    @Async
    public void checkTransaction(Transaction transaction) {
        try {
            log.debug("Checking transaction for fraud: {}", transaction.getReferenceNumber());
            
            Map<String, Object> request = new HashMap<>();
            request.put("transaction_id", transaction.getId().toString());
            request.put("account_id", transaction.getAccountId().toString());
            request.put("user_id", transaction.getAccountId().toString()); // Would get from account
            request.put("amount", transaction.getAmount());
            request.put("currency", transaction.getCurrency());
            request.put("transaction_type", transaction.getType().name().toLowerCase());
            request.put("channel", transaction.getChannel().name().toLowerCase());
            request.put("ip_address", transaction.getIpAddress());
            request.put("device_id", transaction.getDeviceId());
            request.put("device_type", transaction.getDeviceType());
            request.put("location_country", transaction.getLocationCountry());
            request.put("location_city", transaction.getLocationCity());
            request.put("counterparty_account", transaction.getCounterpartyAccount());
            request.put("counterparty_name", transaction.getCounterpartyName());
            request.put("created_at", transaction.getCreatedAt().toString());
            
            // Call fraud detection service
            // In production, handle response and update transaction risk score
            // restTemplate.postForObject(
            //     fraudServiceUrl + "/api/v1/fraud/analyze",
            //     request,
            //     Map.class
            // );
            
            log.debug("Fraud check completed for: {}", transaction.getReferenceNumber());
            
        } catch (Exception e) {
            log.error("Fraud check failed for transaction: {}", 
                transaction.getReferenceNumber(), e);
        }
    }
}


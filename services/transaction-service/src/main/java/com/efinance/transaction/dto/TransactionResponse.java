package com.efinance.transaction.dto;

import com.efinance.transaction.model.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Transaction Response DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TransactionResponse {
    
    private UUID id;
    private UUID accountId;
    private UUID counterpartyAccountId;
    private String referenceNumber;
    private TransactionType type;
    private TransactionChannel channel;
    private Long amount;
    private String currency;
    private Long fee;
    private Long balanceBefore;
    private Long balanceAfter;
    private TransactionStatus status;
    
    // Counterparty
    private String counterpartyName;
    private String counterpartyBank;
    private String counterpartyAccount;
    
    // Description
    private String description;
    private String memo;
    
    // Risk
    private RiskLevel riskLevel;
    private Integer riskScore;
    private Boolean isSuspicious;
    
    // Timestamps
    private LocalDateTime createdAt;
    private LocalDateTime completedAt;
    
    /**
     * Get formatted amount (for display)
     */
    public String getFormattedAmount() {
        return String.format("%.2f %s", amount / 100.0, currency);
    }
}


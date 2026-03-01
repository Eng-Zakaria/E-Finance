package com.efinance.transaction.dto;

import com.efinance.transaction.model.TransactionChannel;
import com.efinance.transaction.model.TransactionType;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * Transaction Request DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TransactionRequest {
    
    @NotNull(message = "Account ID is required")
    private UUID accountId;
    
    private UUID counterpartyAccountId;
    
    @NotNull(message = "Transaction type is required")
    private TransactionType type;
    
    @NotNull(message = "Channel is required")
    private TransactionChannel channel;
    
    @NotNull(message = "Amount is required")
    @Positive(message = "Amount must be positive")
    private Long amount;
    
    @NotNull(message = "Currency is required")
    private String currency;
    
    private Long fee;
    
    @NotNull(message = "Balance before is required")
    private Long balanceBefore;
    
    @NotNull(message = "Balance after is required")
    private Long balanceAfter;
    
    // Counterparty info
    private String counterpartyName;
    private String counterpartyBank;
    private String counterpartyAccount;
    private String counterpartyIban;
    private String counterpartySwift;
    
    // Description
    private String description;
    private String memo;
    
    // Device/Location
    private String ipAddress;
    private String deviceId;
    private String deviceType;
    private String locationCountry;
    private String locationCity;
}


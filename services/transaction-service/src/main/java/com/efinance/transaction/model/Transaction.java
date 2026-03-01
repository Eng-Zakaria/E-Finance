package com.efinance.transaction.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Transaction Entity
 */
@Entity
@Table(name = "transactions", indexes = {
    @Index(name = "idx_transaction_account", columnList = "accountId"),
    @Index(name = "idx_transaction_reference", columnList = "referenceNumber"),
    @Index(name = "idx_transaction_status", columnList = "status"),
    @Index(name = "idx_transaction_created", columnList = "createdAt")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Transaction {
    
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    
    @Column(nullable = false)
    private UUID accountId;
    
    private UUID counterpartyAccountId;
    
    @Column(nullable = false, unique = true, length = 50)
    private String referenceNumber;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private TransactionType type;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private TransactionChannel channel;
    
    @Column(nullable = false)
    private Long amount;  // In cents/smallest unit
    
    @Column(nullable = false, length = 10)
    private String currency;
    
    @Column(nullable = false)
    private Long fee;
    
    @Column(nullable = false)
    private Long balanceBefore;
    
    @Column(nullable = false)
    private Long balanceAfter;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private TransactionStatus status;
    
    // Counterparty info
    private String counterpartyName;
    private String counterpartyBank;
    private String counterpartyAccount;
    private String counterpartyIban;
    private String counterpartySwift;
    
    // Description
    @Column(length = 500)
    private String description;
    
    @Column(length = 255)
    private String memo;
    
    // Location/Device
    @Column(length = 45)
    private String ipAddress;
    
    private String deviceId;
    private String deviceType;
    private String locationCountry;
    private String locationCity;
    
    // Risk/Fraud fields
    @Enumerated(EnumType.STRING)
    @Column(length = 20)
    private RiskLevel riskLevel;
    
    private Integer riskScore;
    
    @Column(nullable = false)
    private Boolean isSuspicious;
    
    private UUID reviewedBy;
    private LocalDateTime reviewedAt;
    
    @Column(length = 1000)
    private String reviewNotes;
    
    // AML fields
    private String amlCheckStatus;
    private String amlAlertId;
    
    // Timestamps
    @CreationTimestamp
    private LocalDateTime createdAt;
    
    @UpdateTimestamp
    private LocalDateTime updatedAt;
    
    private LocalDateTime completedAt;
    
    @PrePersist
    protected void onCreate() {
        if (referenceNumber == null) {
            referenceNumber = generateReferenceNumber();
        }
        if (isSuspicious == null) {
            isSuspicious = false;
        }
        if (fee == null) {
            fee = 0L;
        }
        if (riskLevel == null) {
            riskLevel = RiskLevel.LOW;
        }
        if (riskScore == null) {
            riskScore = 0;
        }
    }
    
    private String generateReferenceNumber() {
        String timestamp = java.time.LocalDateTime.now()
            .format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        String random = UUID.randomUUID().toString().substring(0, 6).toUpperCase();
        return "TXN" + timestamp + random;
    }
}


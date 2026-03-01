package com.efinance.transaction.service;

import com.efinance.transaction.dto.TransactionRequest;
import com.efinance.transaction.dto.TransactionResponse;
import com.efinance.transaction.model.*;
import com.efinance.transaction.repository.TransactionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Transaction Processing Service
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class TransactionService {
    
    private final TransactionRepository transactionRepository;
    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final FraudCheckService fraudCheckService;
    
    /**
     * Process a new transaction
     */
    @Transactional
    public TransactionResponse processTransaction(TransactionRequest request) {
        log.info("Processing transaction: type={}, amount={}, account={}", 
            request.getType(), request.getAmount(), request.getAccountId());
        
        // Create transaction entity
        Transaction transaction = Transaction.builder()
            .accountId(request.getAccountId())
            .counterpartyAccountId(request.getCounterpartyAccountId())
            .type(request.getType())
            .channel(request.getChannel())
            .amount(request.getAmount())
            .currency(request.getCurrency())
            .fee(request.getFee() != null ? request.getFee() : 0L)
            .balanceBefore(request.getBalanceBefore())
            .balanceAfter(request.getBalanceAfter())
            .status(TransactionStatus.PENDING)
            .counterpartyName(request.getCounterpartyName())
            .counterpartyBank(request.getCounterpartyBank())
            .counterpartyAccount(request.getCounterpartyAccount())
            .description(request.getDescription())
            .memo(request.getMemo())
            .ipAddress(request.getIpAddress())
            .deviceId(request.getDeviceId())
            .deviceType(request.getDeviceType())
            .locationCountry(request.getLocationCountry())
            .locationCity(request.getLocationCity())
            .build();
        
        // Save initial transaction
        transaction = transactionRepository.save(transaction);
        
        // Perform fraud check asynchronously
        fraudCheckService.checkTransaction(transaction);
        
        // Update status to processing
        transaction.setStatus(TransactionStatus.PROCESSING);
        transaction = transactionRepository.save(transaction);
        
        // Publish to Kafka for downstream processing
        publishTransactionEvent(transaction, "transaction.created");
        
        log.info("Transaction created: id={}, reference={}", 
            transaction.getId(), transaction.getReferenceNumber());
        
        return mapToResponse(transaction);
    }
    
    /**
     * Complete a transaction
     */
    @Transactional
    public TransactionResponse completeTransaction(UUID transactionId) {
        Transaction transaction = transactionRepository.findById(transactionId)
            .orElseThrow(() -> new RuntimeException("Transaction not found: " + transactionId));
        
        if (transaction.getStatus() != TransactionStatus.PROCESSING) {
            throw new RuntimeException("Transaction is not in processing state");
        }
        
        transaction.setStatus(TransactionStatus.COMPLETED);
        transaction.setCompletedAt(LocalDateTime.now());
        transaction = transactionRepository.save(transaction);
        
        // Publish completion event
        publishTransactionEvent(transaction, "transaction.completed");
        
        log.info("Transaction completed: id={}", transactionId);
        
        return mapToResponse(transaction);
    }
    
    /**
     * Fail a transaction
     */
    @Transactional
    public TransactionResponse failTransaction(UUID transactionId, String reason) {
        Transaction transaction = transactionRepository.findById(transactionId)
            .orElseThrow(() -> new RuntimeException("Transaction not found: " + transactionId));
        
        transaction.setStatus(TransactionStatus.FAILED);
        transaction.setReviewNotes(reason);
        transaction = transactionRepository.save(transaction);
        
        // Publish failure event
        publishTransactionEvent(transaction, "transaction.failed");
        
        log.warn("Transaction failed: id={}, reason={}", transactionId, reason);
        
        return mapToResponse(transaction);
    }
    
    /**
     * Flag transaction for review
     */
    @Transactional
    public TransactionResponse flagTransaction(UUID transactionId, int riskScore, String reason) {
        Transaction transaction = transactionRepository.findById(transactionId)
            .orElseThrow(() -> new RuntimeException("Transaction not found: " + transactionId));
        
        transaction.setStatus(TransactionStatus.FLAGGED);
        transaction.setIsSuspicious(true);
        transaction.setRiskScore(riskScore);
        transaction.setRiskLevel(determineRiskLevel(riskScore));
        transaction.setReviewNotes(reason);
        transaction = transactionRepository.save(transaction);
        
        // Publish flag event
        publishTransactionEvent(transaction, "transaction.flagged");
        
        log.warn("Transaction flagged: id={}, riskScore={}", transactionId, riskScore);
        
        return mapToResponse(transaction);
    }
    
    /**
     * Get transaction by ID
     */
    public Optional<TransactionResponse> getTransaction(UUID transactionId) {
        return transactionRepository.findById(transactionId)
            .map(this::mapToResponse);
    }
    
    /**
     * Get transaction by reference number
     */
    public Optional<TransactionResponse> getByReference(String referenceNumber) {
        return transactionRepository.findByReferenceNumber(referenceNumber)
            .map(this::mapToResponse);
    }
    
    /**
     * Get transactions for account
     */
    public Page<TransactionResponse> getAccountTransactions(UUID accountId, Pageable pageable) {
        return transactionRepository.findByAccountId(accountId, pageable)
            .map(this::mapToResponse);
    }
    
    /**
     * Get flagged transactions
     */
    public Page<TransactionResponse> getFlaggedTransactions(Pageable pageable) {
        return transactionRepository.findByIsSuspiciousTrue(pageable)
            .map(this::mapToResponse);
    }
    
    /**
     * Get daily transaction volume for account
     */
    public Long getDailyVolume(UUID accountId) {
        LocalDateTime since = LocalDateTime.now().minusHours(24);
        return transactionRepository.sumAmountByAccountIdAndTypesSince(
            accountId,
            List.of(TransactionType.TRANSFER_OUT, TransactionType.PAYMENT, TransactionType.WITHDRAWAL),
            since
        );
    }
    
    /**
     * Get daily transaction count for account
     */
    public Long getDailyCount(UUID accountId) {
        LocalDateTime since = LocalDateTime.now().minusHours(24);
        return transactionRepository.countByAccountIdSince(accountId, since);
    }
    
    private RiskLevel determineRiskLevel(int riskScore) {
        if (riskScore >= 90) return RiskLevel.CRITICAL;
        if (riskScore >= 70) return RiskLevel.HIGH;
        if (riskScore >= 50) return RiskLevel.MEDIUM;
        return RiskLevel.LOW;
    }
    
    private void publishTransactionEvent(Transaction transaction, String eventType) {
        try {
            kafkaTemplate.send("transactions", transaction.getReferenceNumber(), 
                mapToResponse(transaction));
            log.debug("Published event: type={}, reference={}", 
                eventType, transaction.getReferenceNumber());
        } catch (Exception e) {
            log.error("Failed to publish transaction event", e);
        }
    }
    
    private TransactionResponse mapToResponse(Transaction tx) {
        return TransactionResponse.builder()
            .id(tx.getId())
            .accountId(tx.getAccountId())
            .counterpartyAccountId(tx.getCounterpartyAccountId())
            .referenceNumber(tx.getReferenceNumber())
            .type(tx.getType())
            .channel(tx.getChannel())
            .amount(tx.getAmount())
            .currency(tx.getCurrency())
            .fee(tx.getFee())
            .balanceBefore(tx.getBalanceBefore())
            .balanceAfter(tx.getBalanceAfter())
            .status(tx.getStatus())
            .counterpartyName(tx.getCounterpartyName())
            .counterpartyBank(tx.getCounterpartyBank())
            .counterpartyAccount(tx.getCounterpartyAccount())
            .description(tx.getDescription())
            .memo(tx.getMemo())
            .riskLevel(tx.getRiskLevel())
            .riskScore(tx.getRiskScore())
            .isSuspicious(tx.getIsSuspicious())
            .createdAt(tx.getCreatedAt())
            .completedAt(tx.getCompletedAt())
            .build();
    }
}


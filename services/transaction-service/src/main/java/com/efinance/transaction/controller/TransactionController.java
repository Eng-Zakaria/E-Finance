package com.efinance.transaction.controller;

import com.efinance.transaction.dto.TransactionRequest;
import com.efinance.transaction.dto.TransactionResponse;
import com.efinance.transaction.service.TransactionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

/**
 * Transaction REST Controller
 */
@RestController
@RequestMapping("/api/v1/transactions")
@RequiredArgsConstructor
@Tag(name = "Transactions", description = "Transaction processing endpoints")
public class TransactionController {
    
    private final TransactionService transactionService;
    
    @PostMapping
    @Operation(summary = "Process a new transaction")
    public ResponseEntity<TransactionResponse> processTransaction(
            @Valid @RequestBody TransactionRequest request) {
        TransactionResponse response = transactionService.processTransaction(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
    
    @GetMapping("/{id}")
    @Operation(summary = "Get transaction by ID")
    public ResponseEntity<TransactionResponse> getTransaction(@PathVariable UUID id) {
        return transactionService.getTransaction(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
    
    @GetMapping("/reference/{referenceNumber}")
    @Operation(summary = "Get transaction by reference number")
    public ResponseEntity<TransactionResponse> getByReference(
            @PathVariable String referenceNumber) {
        return transactionService.getByReference(referenceNumber)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
    
    @GetMapping("/account/{accountId}")
    @Operation(summary = "Get transactions for an account")
    public ResponseEntity<Page<TransactionResponse>> getAccountTransactions(
            @PathVariable UUID accountId,
            @PageableDefault(size = 20) Pageable pageable) {
        Page<TransactionResponse> transactions = 
            transactionService.getAccountTransactions(accountId, pageable);
        return ResponseEntity.ok(transactions);
    }
    
    @PostMapping("/{id}/complete")
    @Operation(summary = "Complete a transaction")
    public ResponseEntity<TransactionResponse> completeTransaction(@PathVariable UUID id) {
        TransactionResponse response = transactionService.completeTransaction(id);
        return ResponseEntity.ok(response);
    }
    
    @PostMapping("/{id}/fail")
    @Operation(summary = "Fail a transaction")
    public ResponseEntity<TransactionResponse> failTransaction(
            @PathVariable UUID id,
            @RequestParam String reason) {
        TransactionResponse response = transactionService.failTransaction(id, reason);
        return ResponseEntity.ok(response);
    }
    
    @PostMapping("/{id}/flag")
    @Operation(summary = "Flag a transaction for review")
    public ResponseEntity<TransactionResponse> flagTransaction(
            @PathVariable UUID id,
            @RequestParam int riskScore,
            @RequestParam String reason) {
        TransactionResponse response = transactionService.flagTransaction(id, riskScore, reason);
        return ResponseEntity.ok(response);
    }
    
    @GetMapping("/flagged")
    @Operation(summary = "Get flagged transactions")
    public ResponseEntity<Page<TransactionResponse>> getFlaggedTransactions(
            @PageableDefault(size = 20) Pageable pageable) {
        Page<TransactionResponse> transactions = 
            transactionService.getFlaggedTransactions(pageable);
        return ResponseEntity.ok(transactions);
    }
    
    @GetMapping("/account/{accountId}/volume")
    @Operation(summary = "Get daily transaction volume for account")
    public ResponseEntity<Map<String, Object>> getDailyVolume(@PathVariable UUID accountId) {
        Long volume = transactionService.getDailyVolume(accountId);
        Long count = transactionService.getDailyCount(accountId);
        
        return ResponseEntity.ok(Map.of(
            "accountId", accountId,
            "dailyVolume", volume != null ? volume : 0,
            "dailyCount", count != null ? count : 0,
            "period", "24h"
        ));
    }
}


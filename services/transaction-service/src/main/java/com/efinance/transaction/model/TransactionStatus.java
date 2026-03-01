package com.efinance.transaction.model;

/**
 * Transaction Status
 */
public enum TransactionStatus {
    PENDING,
    PROCESSING,
    COMPLETED,
    FAILED,
    CANCELLED,
    REVERSED,
    ON_HOLD,
    FLAGGED
}


package com.efinance.transaction.repository;

import com.efinance.transaction.model.Transaction;
import com.efinance.transaction.model.TransactionStatus;
import com.efinance.transaction.model.TransactionType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Transaction Repository
 */
@Repository
public interface TransactionRepository extends JpaRepository<Transaction, UUID> {
    
    Optional<Transaction> findByReferenceNumber(String referenceNumber);
    
    Page<Transaction> findByAccountId(UUID accountId, Pageable pageable);
    
    Page<Transaction> findByAccountIdAndStatus(UUID accountId, TransactionStatus status, Pageable pageable);
    
    List<Transaction> findByAccountIdAndCreatedAtBetween(
        UUID accountId, 
        LocalDateTime start, 
        LocalDateTime end
    );
    
    @Query("SELECT t FROM Transaction t WHERE t.accountId = :accountId " +
           "AND t.createdAt >= :since ORDER BY t.createdAt DESC")
    List<Transaction> findRecentByAccountId(
        @Param("accountId") UUID accountId, 
        @Param("since") LocalDateTime since
    );
    
    @Query("SELECT SUM(t.amount) FROM Transaction t WHERE t.accountId = :accountId " +
           "AND t.type IN :types AND t.status = 'COMPLETED' " +
           "AND t.createdAt >= :since")
    Long sumAmountByAccountIdAndTypesSince(
        @Param("accountId") UUID accountId,
        @Param("types") List<TransactionType> types,
        @Param("since") LocalDateTime since
    );
    
    @Query("SELECT COUNT(t) FROM Transaction t WHERE t.accountId = :accountId " +
           "AND t.createdAt >= :since")
    Long countByAccountIdSince(
        @Param("accountId") UUID accountId,
        @Param("since") LocalDateTime since
    );
    
    Page<Transaction> findByIsSuspiciousTrue(Pageable pageable);
    
    Page<Transaction> findByStatus(TransactionStatus status, Pageable pageable);
    
    @Query("SELECT t FROM Transaction t WHERE t.status = :status " +
           "AND t.createdAt < :before")
    List<Transaction> findStaleTransactions(
        @Param("status") TransactionStatus status,
        @Param("before") LocalDateTime before
    );
}


"""
Spark Analytics Jobs
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
import structlog

from app.config import settings
from app.spark.session import get_spark_session

logger = structlog.get_logger(__name__)


class TransactionAnalytics:
    """Transaction analytics using Spark"""
    
    def __init__(self):
        self.spark = get_spark_session()
    
    def load_transactions(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> DataFrame:
        """Load transactions from database"""
        # In production, would load from actual database
        # For demo, create sample data
        
        data = [
            ("tx1", "acc1", "transfer_out", 10000, "USD", "2024-01-15", "completed"),
            ("tx2", "acc1", "deposit", 50000, "USD", "2024-01-16", "completed"),
            ("tx3", "acc2", "payment", 2500, "USD", "2024-01-16", "completed"),
            ("tx4", "acc1", "withdrawal", 5000, "USD", "2024-01-17", "completed"),
            ("tx5", "acc3", "transfer_in", 100000, "USD", "2024-01-17", "completed"),
        ]
        
        columns = ["id", "account_id", "type", "amount", "currency", "date", "status"]
        
        return self.spark.createDataFrame(data, columns)
    
    def calculate_daily_volume(self, df: DataFrame) -> DataFrame:
        """Calculate daily transaction volume"""
        return (
            df
            .groupBy("date", "type")
            .agg(
                F.count("id").alias("transaction_count"),
                F.sum("amount").alias("total_amount"),
                F.avg("amount").alias("avg_amount")
            )
            .orderBy("date")
        )
    
    def calculate_account_summary(self, df: DataFrame) -> DataFrame:
        """Calculate account-level summary"""
        return (
            df
            .groupBy("account_id")
            .agg(
                F.count("id").alias("total_transactions"),
                F.sum(F.when(F.col("type").isin(["deposit", "transfer_in"]), F.col("amount")).otherwise(0)).alias("total_credits"),
                F.sum(F.when(F.col("type").isin(["withdrawal", "transfer_out", "payment"]), F.col("amount")).otherwise(0)).alias("total_debits"),
                F.max("date").alias("last_transaction_date")
            )
        )
    
    def detect_anomalies(self, df: DataFrame) -> DataFrame:
        """Detect anomalous transactions using statistical methods"""
        # Calculate mean and std per account
        stats = (
            df
            .groupBy("account_id")
            .agg(
                F.avg("amount").alias("mean_amount"),
                F.stddev("amount").alias("std_amount")
            )
        )
        
        # Join and calculate z-score
        return (
            df
            .join(stats, "account_id")
            .withColumn(
                "z_score",
                (F.col("amount") - F.col("mean_amount")) / F.col("std_amount")
            )
            .withColumn(
                "is_anomaly",
                F.abs(F.col("z_score")) > 3
            )
            .filter(F.col("is_anomaly") == True)
            .select("id", "account_id", "amount", "type", "z_score")
        )
    
    def calculate_trend(self, df: DataFrame, window_days: int = 7) -> DataFrame:
        """Calculate moving average trend"""
        window = Window.partitionBy("account_id").orderBy("date").rowsBetween(-window_days, 0)
        
        return (
            df
            .withColumn("moving_avg", F.avg("amount").over(window))
            .withColumn("moving_sum", F.sum("amount").over(window))
        )


class RiskAnalytics:
    """Risk analytics using Spark"""
    
    def __init__(self):
        self.spark = get_spark_session()
    
    def calculate_risk_scores(self, transactions_df: DataFrame) -> DataFrame:
        """Calculate risk scores for accounts"""
        
        # Risk factors
        risk_df = (
            transactions_df
            .groupBy("account_id")
            .agg(
                F.count("id").alias("tx_count"),
                F.sum("amount").alias("total_volume"),
                F.max("amount").alias("max_transaction"),
                F.countDistinct("type").alias("tx_type_diversity")
            )
        )
        
        # Normalize and calculate score
        return (
            risk_df
            .withColumn(
                "volume_score",
                F.when(F.col("total_volume") > 100000, 30)
                .when(F.col("total_volume") > 50000, 20)
                .when(F.col("total_volume") > 10000, 10)
                .otherwise(5)
            )
            .withColumn(
                "frequency_score",
                F.when(F.col("tx_count") > 50, 25)
                .when(F.col("tx_count") > 20, 15)
                .otherwise(5)
            )
            .withColumn(
                "risk_score",
                F.col("volume_score") + F.col("frequency_score")
            )
        )


class CustomerAnalytics:
    """Customer segmentation and analytics"""
    
    def __init__(self):
        self.spark = get_spark_session()
    
    def segment_customers(self, transactions_df: DataFrame) -> DataFrame:
        """Segment customers based on behavior"""
        
        customer_metrics = (
            transactions_df
            .groupBy("account_id")
            .agg(
                F.count("id").alias("frequency"),
                F.sum("amount").alias("monetary"),
                F.datediff(F.current_date(), F.max("date")).alias("recency")
            )
        )
        
        # Simple segmentation based on RFM
        return (
            customer_metrics
            .withColumn(
                "segment",
                F.when(
                    (F.col("frequency") > 10) & (F.col("monetary") > 50000),
                    "high_value"
                )
                .when(
                    (F.col("frequency") > 5) & (F.col("monetary") > 20000),
                    "medium_value"
                )
                .when(
                    F.col("recency") > 30,
                    "at_risk"
                )
                .otherwise("standard")
            )
        )


# Global instances
transaction_analytics = TransactionAnalytics()
risk_analytics = RiskAnalytics()
customer_analytics = CustomerAnalytics()


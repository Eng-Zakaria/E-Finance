"""
Spark Session Management
"""
from pyspark.sql import SparkSession
from app.config import settings

_spark_session = None


def get_spark_session() -> SparkSession:
    """Get or create Spark session"""
    global _spark_session
    
    if _spark_session is None:
        _spark_session = (
            SparkSession.builder
            .appName(settings.SPARK_APP_NAME)
            .master(settings.SPARK_MASTER)
            .config("spark.driver.memory", settings.SPARK_DRIVER_MEMORY)
            .config("spark.executor.memory", settings.SPARK_EXECUTOR_MEMORY)
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0,org.postgresql:postgresql:42.6.0")
            .getOrCreate()
        )
        
        _spark_session.sparkContext.setLogLevel("WARN")
    
    return _spark_session


def stop_spark_session():
    """Stop Spark session"""
    global _spark_session
    if _spark_session is not None:
        _spark_session.stop()
        _spark_session = None


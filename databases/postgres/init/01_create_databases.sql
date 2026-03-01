-- Create additional databases for services
CREATE DATABASE efinance_fraud;
CREATE DATABASE efinance_web3;
CREATE DATABASE efinance_bnpl;
CREATE DATABASE efinance_transactions;
CREATE DATABASE efinance_airflow;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE efinance_fraud TO efinance;
GRANT ALL PRIVILEGES ON DATABASE efinance_web3 TO efinance;
GRANT ALL PRIVILEGES ON DATABASE efinance_bnpl TO efinance;
GRANT ALL PRIVILEGES ON DATABASE efinance_transactions TO efinance;
GRANT ALL PRIVILEGES ON DATABASE efinance_airflow TO efinance;


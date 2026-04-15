package com.example.samples;

/**
 * HARDCODED SECRETS - Examples of credentials embedded directly in source code.
 *
 * Passwords, API keys, tokens, and connection strings should never appear as
 * string literals in source files. They should be loaded from environment
 * variables, secret vaults, or encrypted configuration files at runtime.
 *
 * This sample demonstrates common patterns that the security debt detector
 * should flag as category 8 (Hardcoded Secrets).
 */

import java.sql.Connection;
import java.sql.DriverManager;
import java.util.Properties;

// ============================================================================
// Example 1: Database credentials hardcoded in a configuration class
// ============================================================================

class DatabaseConfig {
    // These should come from environment variables or a vault
    private static final String DB_HOST = "prod-db.internal.corp";
    private static final String DB_PORT = "3306";
    private static final String DB_NAME = "customer_data";
    private static final String DB_USER = "admin";
    private static final String DB_PASSWORD = "SuperS3cret!Prod2024";

    // JDBC connection string with embedded credentials
    private static final String JDBC_URL =
        "jdbc:mysql://admin:SuperS3cret!Prod2024@prod-db.internal.corp:3306/customer_data";

    public Connection getConnection() throws Exception {
        return DriverManager.getConnection(
            "jdbc:mysql://" + DB_HOST + ":" + DB_PORT + "/" + DB_NAME,
            DB_USER, DB_PASSWORD);
    }
}


// ============================================================================
// Example 2: API keys and tokens hardcoded in a service class
// ============================================================================

class PaymentGateway {
    // Hardcoded API keys — a critical security vulnerability
    private static final String STRIPE_API_KEY = "sk_live_51HG3xKLmno4pQrStuVwXyZ";
    private static final String STRIPE_SECRET  = "whsec_abc123def456ghi789jkl012mno345";
    private static final String PAYPAL_CLIENT_ID = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPp";
    private static final String PAYPAL_SECRET    = "EeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTt";

    public void processPayment(double amount, String currency) {
        // Uses hardcoded keys to initialize the client
        Properties props = new Properties();
        props.setProperty("api_key", STRIPE_API_KEY);
        props.setProperty("secret", STRIPE_SECRET);
        // ... payment processing logic ...
    }

    public boolean verifyWebhook(String payload, String signature) {
        // Hardcoded webhook secret used for verification
        String webhookSecret = "whsec_abc123def456ghi789jkl012mno345";
        // ... verification logic ...
        return true;
    }
}


// ============================================================================
// Example 3: AWS credentials and private keys in source
// ============================================================================

class CloudStorageClient {
    private String awsAccessKey = "AKIAIOSFODNN7EXAMPLE";
    private String awsSecretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";
    private String region = "us-east-1";

    // Private key embedded directly in source (should be in a keystore)
    private static final String PRIVATE_KEY =
        "-----BEGIN RSA PRIVATE KEY-----\n" +
        "MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy5EXAMPLE\n" +
        "-----END RSA PRIVATE KEY-----";

    private String authToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.EXAMPLE";

    public void uploadFile(String bucket, String key, byte[] data) {
        // Uses hardcoded credentials to authenticate
        // ... upload logic with awsAccessKey and awsSecretKey ...
    }
}

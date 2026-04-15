using System;
using System.Data.SqlClient;
using System.Collections.Generic;

/// <summary>
/// HARDCODED SECRETS - Examples of credentials embedded directly in source code.
///
/// Passwords, API keys, tokens, and connection strings should never appear as
/// string literals in source files. They should be loaded from environment
/// variables, secret vaults, or encrypted configuration files at runtime.
/// </summary>

// ============================================================================
// Example 1: Database credentials hardcoded in a configuration class
// ============================================================================

public class DatabaseConfig
{
    // These should come from environment variables or a vault
    private const string DbHost     = "prod-db.internal.corp";
    private const string DbPort     = "1433";
    private const string DbName     = "customer_data";
    private const string DbUser     = "admin";
    private const string DbPassword = "SuperS3cret!Prod2024";

    // Connection string with embedded credentials
    private const string ConnectionString =
        "Server=prod-db.internal.corp,1433;Database=customer_data;User Id=admin;Password=SuperS3cret!Prod2024;";

    public SqlConnection GetConnection()
    {
        return new SqlConnection(
            $"Server={DbHost},{DbPort};Database={DbName};User Id={DbUser};Password={DbPassword};");
    }
}


// ============================================================================
// Example 2: API keys and tokens hardcoded in a service class
// ============================================================================

public class PaymentGateway
{
    // Hardcoded API keys — a critical security vulnerability
    private const string StripeApiKey    = "sk_live_51HG3xKLmno4pQrStuVwXyZ";
    private const string StripeSecret    = "whsec_abc123def456ghi789jkl012mno345";
    private const string PayPalClientId  = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPp";
    private const string PayPalSecret    = "EeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTt";

    public void ProcessPayment(double amount, string currency)
    {
        // Uses hardcoded keys to initialise the client
        var config = new Dictionary<string, string>
        {
            { "api_key", StripeApiKey },
            { "secret",  StripeSecret }
        };
        // ... payment processing logic ...
    }

    public bool VerifyWebhook(string payload, string signature)
    {
        // Hardcoded webhook secret used for verification
        string webhookSecret = "whsec_abc123def456ghi789jkl012mno345";
        // ... verification logic ...
        return true;
    }
}


// ============================================================================
// Example 3: Cloud credentials and private keys in source
// ============================================================================

public class CloudStorageClient
{
    private string awsAccessKey = "AKIAIOSFODNN7EXAMPLE";
    private string awsSecretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";
    private string region = "us-east-1";

    // Private key embedded directly in source (should be in a keystore)
    private const string PrivateKey =
        "-----BEGIN RSA PRIVATE KEY-----\n" +
        "MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy5EXAMPLE\n" +
        "-----END RSA PRIVATE KEY-----";

    private string authToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.EXAMPLE";

    public void UploadFile(string bucket, string key, byte[] data)
    {
        // Uses hardcoded credentials to authenticate
        // ... upload logic with awsAccessKey and awsSecretKey ...
    }
}

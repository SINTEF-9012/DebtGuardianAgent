using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Diagnostics;

/// <summary>
/// SQL/COMMAND INJECTION - Examples of unsanitised user input in queries and commands.
///
/// User-controlled input concatenated directly into SQL queries or OS commands
/// enables injection attacks. Parameterised queries (SqlParameter) and
/// Process with argument arrays should be used instead.
/// </summary>

// ============================================================================
// Example 1: SQL injection via string concatenation
// ============================================================================

public class UserRepository
{
    private SqlConnection connection;

    /// <summary>
    /// VULNERABLE: username is concatenated directly into the SQL string.
    /// An attacker can supply: ' OR '1'='1' --
    /// </summary>
    public SqlDataReader FindByUsername(string username)
    {
        string sql = "SELECT * FROM users WHERE username = '" + username + "'";
        var cmd = new SqlCommand(sql, connection);
        return cmd.ExecuteReader();
    }

    /// <summary>
    /// VULNERABLE: both userId and role are concatenated without parameterisation.
    /// </summary>
    public void UpdateUserRole(string userId, string role)
    {
        string sql = "UPDATE users SET role = '" + role + "' WHERE id = " + userId;
        var cmd = new SqlCommand(sql, connection);
        cmd.ExecuteNonQuery();
    }

    /// <summary>
    /// VULNERABLE: DELETE with concatenated input.
    /// </summary>
    public void DeleteUser(string userId)
    {
        string sql = "DELETE FROM users WHERE id = " + userId;
        new SqlCommand(sql, connection).ExecuteNonQuery();
    }

    /// <summary>
    /// VULNERABLE: search term concatenated into LIKE clause.
    /// </summary>
    public List<string> SearchUsers(string searchTerm)
    {
        string sql = "SELECT name FROM users WHERE name LIKE '%" + searchTerm + "%'";
        var cmd = new SqlCommand(sql, connection);
        var reader = cmd.ExecuteReader();
        var results = new List<string>();
        while (reader.Read())
        {
            results.Add(reader.GetString(0));
        }
        return results;
    }
}


// ============================================================================
// Example 2: OS command injection via Process.Start
// ============================================================================

public class ReportService
{
    /// <summary>
    /// VULNERABLE: reportName is concatenated directly into a shell command.
    /// An attacker can supply: "; rm -rf / #
    /// </summary>
    public void GenerateReport(string reportName)
    {
        string cmd = "/usr/local/bin/generate_report.sh " + reportName;
        Process.Start("bash", "-c \"" + cmd + "\"");
    }

    /// <summary>
    /// VULNERABLE: filename from user input used in command.
    /// </summary>
    public string ConvertDocument(string inputFile, string outputFormat)
    {
        string cmd = "pandoc " + inputFile + " -o output." + outputFormat;
        var process = Process.Start("bash", "-c \"" + cmd + "\"");
        process.WaitForExit();
        return "output." + outputFormat;
    }
}


// ============================================================================
// Example 3: Mixed SQL and command injection in a single class
// ============================================================================

public class AdminPanel
{
    private SqlConnection connection;

    /// <summary>
    /// VULNERABLE: table name from user input — enables SQL injection.
    /// </summary>
    public SqlDataReader ExportTable(string tableName)
    {
        string sql = "SELECT * FROM " + tableName;
        return new SqlCommand(sql, connection).ExecuteReader();
    }

    /// <summary>
    /// VULNERABLE: user-supplied IP address injected into ping command.
    /// </summary>
    public void PingHost(string ipAddress)
    {
        string cmd = "ping -c 4 " + ipAddress;
        Process.Start("bash", "-c \"" + cmd + "\"");
    }

    /// <summary>
    /// VULNERABLE: log query built via concatenation with user date input.
    /// </summary>
    public SqlDataReader GetLogsByDate(string startDate, string endDate)
    {
        string sql = "SELECT * FROM audit_log WHERE created_at BETWEEN '"
                   + startDate + "' AND '" + endDate + "'";
        return new SqlCommand(sql, connection).ExecuteReader();
    }
}

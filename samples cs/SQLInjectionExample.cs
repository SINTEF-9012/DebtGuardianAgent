using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Diagnostics;

// --- UserRepository — database access layer ---

public class UserRepository
{
    private SqlConnection connection;

    public SqlDataReader FindByUsername(string username)
    {
        string sql = "SELECT * FROM users WHERE username = '" + username + "'";
        var cmd = new SqlCommand(sql, connection);
        return cmd.ExecuteReader();
    }

    public void UpdateUserRole(string userId, string role)
    {
        string sql = "UPDATE users SET role = '" + role + "' WHERE id = " + userId;
        var cmd = new SqlCommand(sql, connection);
        cmd.ExecuteNonQuery();
    }

    public void DeleteUser(string userId)
    {
        string sql = "DELETE FROM users WHERE id = " + userId;
        new SqlCommand(sql, connection).ExecuteNonQuery();
    }

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


// --- ReportService — report generation ---

public class ReportService
{
    public void GenerateReport(string reportName)
    {
        string cmd = "/usr/local/bin/generate_report.sh " + reportName;
        Process.Start("bash", "-c \"" + cmd + "\"");
    }

    public string ConvertDocument(string inputFile, string outputFormat)
    {
        string cmd = "pandoc " + inputFile + " -o output." + outputFormat;
        var process = Process.Start("bash", "-c \"" + cmd + "\"");
        process.WaitForExit();
        return "output." + outputFormat;
    }
}


// --- AdminPanel — administrative operations ---

public class AdminPanel
{
    private SqlConnection connection;

    public SqlDataReader ExportTable(string tableName)
    {
        string sql = "SELECT * FROM " + tableName;
        return new SqlCommand(sql, connection).ExecuteReader();
    }

    public void PingHost(string ipAddress)
    {
        string cmd = "ping -c 4 " + ipAddress;
        Process.Start("bash", "-c \"" + cmd + "\"");
    }

    public SqlDataReader GetLogsByDate(string startDate, string endDate)
    {
        string sql = "SELECT * FROM audit_log WHERE created_at BETWEEN '"
                   + startDate + "' AND '" + endDate + "'";
        return new SqlCommand(sql, connection).ExecuteReader();
    }
}

package com.example.samples;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.List;
import java.util.ArrayList;

/**
 * SQL/COMMAND INJECTION - Examples of unsanitised user input in queries and commands.
 *
 * User-controlled input concatenated directly into SQL queries or OS commands
 * enables injection attacks. Parameterised queries (PreparedStatement) and
 * process builder APIs with argument arrays should be used instead.
 *
 * This sample demonstrates common patterns that the security debt detector
 * should flag as category 9 (SQL/Command Injection).
 */

// ============================================================================
// Example 1: SQL injection via string concatenation
// ============================================================================

class UserRepository {
    private Connection connection;

    /**
     * VULNERABLE: username is concatenated directly into the SQL string.
     * An attacker can supply: ' OR '1'='1' --
     */
    public ResultSet findByUsername(String username) throws Exception {
        String sql = "SELECT * FROM users WHERE username = '" + username + "'";
        Statement stmt = connection.createStatement();
        return stmt.executeQuery(sql);
    }

    /**
     * VULNERABLE: both userId and role are concatenated without parameterisation.
     */
    public void updateUserRole(String userId, String role) throws Exception {
        String sql = "UPDATE users SET role = '" + role + "' WHERE id = " + userId;
        Statement stmt = connection.createStatement();
        stmt.executeUpdate(sql);
    }

    /**
     * VULNERABLE: DELETE with concatenated input.
     */
    public void deleteUser(String userId) throws Exception {
        String sql = "DELETE FROM users WHERE id = " + userId;
        connection.createStatement().execute(sql);
    }

    /**
     * VULNERABLE: search term concatenated into LIKE clause.
     */
    public List<String> searchUsers(String searchTerm) throws Exception {
        String sql = "SELECT name FROM users WHERE name LIKE '%" + searchTerm + "%'";
        ResultSet rs = connection.createStatement().executeQuery(sql);
        List<String> results = new ArrayList<>();
        while (rs.next()) {
            results.add(rs.getString("name"));
        }
        return results;
    }
}


// ============================================================================
// Example 2: OS command injection via Runtime.exec
// ============================================================================

class ReportService {
    /**
     * VULNERABLE: reportName is concatenated directly into a shell command.
     * An attacker can supply: "; rm -rf / #
     */
    public void generateReport(String reportName) throws Exception {
        String cmd = "/usr/local/bin/generate_report.sh " + reportName;
        Runtime.getRuntime().exec(cmd);
    }

    /**
     * VULNERABLE: filename from user input used in command.
     */
    public byte[] convertDocument(String inputFile, String outputFormat) throws Exception {
        String cmd = "pandoc " + inputFile + " -o output." + outputFormat;
        Process process = Runtime.getRuntime().exec(cmd);
        return process.getInputStream().readAllBytes();
    }
}


// ============================================================================
// Example 3: Mixed SQL and command injection in a single class
// ============================================================================

class AdminPanel {
    private Connection connection;

    /**
     * VULNERABLE: table name from user input — enables SQL injection.
     */
    public ResultSet exportTable(String tableName) throws Exception {
        String sql = "SELECT * FROM " + tableName;
        return connection.createStatement().executeQuery(sql);
    }

    /**
     * VULNERABLE: user-supplied IP address injected into ping command.
     */
    public String pingHost(String ipAddress) throws Exception {
        String cmd = "ping -c 4 " + ipAddress;
        Process process = Runtime.getRuntime().exec(cmd);
        return new String(process.getInputStream().readAllBytes());
    }

    /**
     * VULNERABLE: log query built via concatenation with user date input.
     */
    public ResultSet getLogsByDate(String startDate, String endDate) throws Exception {
        String sql = "SELECT * FROM audit_log WHERE created_at BETWEEN '"
                   + startDate + "' AND '" + endDate + "'";
        return connection.createStatement().executeQuery(sql);
    }
}

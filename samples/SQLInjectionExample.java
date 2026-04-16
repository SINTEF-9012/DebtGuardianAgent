package com.example.samples;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.List;
import java.util.ArrayList;

// --- UserRepository — database access layer ---

class UserRepository {
    private Connection connection;

    public ResultSet findByUsername(String username) throws Exception {
        String sql = "SELECT * FROM users WHERE username = '" + username + "'";
        Statement stmt = connection.createStatement();
        return stmt.executeQuery(sql);
    }

    public void updateUserRole(String userId, String role) throws Exception {
        String sql = "UPDATE users SET role = '" + role + "' WHERE id = " + userId;
        Statement stmt = connection.createStatement();
        stmt.executeUpdate(sql);
    }

    public void deleteUser(String userId) throws Exception {
        String sql = "DELETE FROM users WHERE id = " + userId;
        connection.createStatement().execute(sql);
    }

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


// --- ReportService — report generation ---

class ReportService {
    public void generateReport(String reportName) throws Exception {
        String cmd = "/usr/local/bin/generate_report.sh " + reportName;
        Runtime.getRuntime().exec(cmd);
    }

    public byte[] convertDocument(String inputFile, String outputFormat) throws Exception {
        String cmd = "pandoc " + inputFile + " -o output." + outputFormat;
        Process process = Runtime.getRuntime().exec(cmd);
        return process.getInputStream().readAllBytes();
    }
}


// --- AdminPanel — administrative operations ---

class AdminPanel {
    private Connection connection;

    public ResultSet exportTable(String tableName) throws Exception {
        String sql = "SELECT * FROM " + tableName;
        return connection.createStatement().executeQuery(sql);
    }

    public String pingHost(String ipAddress) throws Exception {
        String cmd = "ping -c 4 " + ipAddress;
        Process process = Runtime.getRuntime().exec(cmd);
        return new String(process.getInputStream().readAllBytes());
    }

    public ResultSet getLogsByDate(String startDate, String endDate) throws Exception {
        String sql = "SELECT * FROM audit_log WHERE created_at BETWEEN '"
                   + startDate + "' AND '" + endDate + "'";
        return connection.createStatement().executeQuery(sql);
    }
}

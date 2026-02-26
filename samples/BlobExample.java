package com.example.samples;

import java.util.List;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.sql.Connection;
import java.sql.Statement;
import java.sql.ResultSet;

/**
 * OrderManager - Example of Blob (God Class) code smell
 * This class has too many responsibilities and should be split
 */
public class OrderManager {
    private Connection database;
    private EmailService emailService;
    private Logger logger;
    private PaymentGateway paymentGateway;
    private InventorySystem inventory;
    private Map<String, Order> orderCache;
    
    public OrderManager() {
        this.orderCache = new HashMap<>();
        this.logger = new Logger("OrderManager");
    }
    
    // Order CRUD operations
    public void createOrder(Order order) {
        try {
            validateOrder(order);
            saveToDatabase(order);
            updateInventory(order);
            sendOrderConfirmation(order);
            orderCache.put(order.getId(), order);
            logger.log("Order created: " + order.getId());
        } catch (Exception e) {
            logger.error("Failed to create order", e);
        }
    }
    
    public void updateOrder(Order order) {
        if (!orderCache.containsKey(order.getId())) {
            logger.warn("Order not in cache: " + order.getId());
        }
        try {
            Statement stmt = database.createStatement();
            stmt.execute("UPDATE orders SET status='" + order.getStatus() + 
                        "' WHERE id='" + order.getId() + "'");
            orderCache.put(order.getId(), order);
        } catch (Exception e) {
            logger.error("Update failed", e);
        }
    }
    
    public void deleteOrder(String orderId) {
        try {
            Statement stmt = database.createStatement();
            stmt.execute("DELETE FROM orders WHERE id='" + orderId + "'");
            orderCache.remove(orderId);
            logger.log("Order deleted: " + orderId);
        } catch (Exception e) {
            logger.error("Delete failed", e);
        }
    }
    
    public List<Order> findOrders(String criteria) {
        List<Order> results = new ArrayList<>();
        try {
            Statement stmt = database.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT * FROM orders WHERE " + criteria);
            while (rs.next()) {
                Order order = new Order();
                order.setId(rs.getString("id"));
                order.setCustomerId(rs.getString("customer_id"));
                order.setStatus(rs.getString("status"));
                results.add(order);
            }
        } catch (Exception e) {
            logger.error("Find failed", e);
        }
        return results;
    }
    
    // Payment processing
    public boolean processPayment(Payment payment) {
        try {
            if (payment.getAmount() <= 0) {
                return false;
            }
            boolean result = paymentGateway.charge(payment);
            if (result) {
                updateOrderStatus(payment.getOrderId(), "PAID");
                sendPaymentConfirmation(payment);
            }
            return result;
        } catch (Exception e) {
            logger.error("Payment processing failed", e);
            return false;
        }
    }
    
    public void refundPayment(String paymentId) {
        try {
            Payment payment = findPayment(paymentId);
            paymentGateway.refund(payment);
            updateOrderStatus(payment.getOrderId(), "REFUNDED");
            sendRefundNotification(payment);
        } catch (Exception e) {
            logger.error("Refund failed", e);
        }
    }
    
    // Notification handling
    public void sendOrderConfirmation(Order order) {
        String message = "Your order " + order.getId() + " has been confirmed.";
        emailService.send(order.getCustomerEmail(), "Order Confirmation", message);
    }
    
    public void sendShippingNotification(Order order) {
        String message = "Your order " + order.getId() + " has been shipped.";
        emailService.send(order.getCustomerEmail(), "Shipping Update", message);
    }
    
    public void sendPaymentConfirmation(Payment payment) {
        String message = "Payment received: $" + payment.getAmount();
        emailService.send(payment.getCustomerEmail(), "Payment Confirmation", message);
    }
    
    public void sendRefundNotification(Payment payment) {
        String message = "Refund processed: $" + payment.getAmount();
        emailService.send(payment.getCustomerEmail(), "Refund Processed", message);
    }
    
    // Reporting
    public Report generateSalesReport(String startDate, String endDate) {
        Report report = new Report();
        try {
            Statement stmt = database.createStatement();
            ResultSet rs = stmt.executeQuery(
                "SELECT SUM(amount) as total FROM orders WHERE date BETWEEN '" + 
                startDate + "' AND '" + endDate + "'"
            );
            if (rs.next()) {
                report.setTotalSales(rs.getDouble("total"));
            }
            report.setTitle("Sales Report: " + startDate + " to " + endDate);
        } catch (Exception e) {
            logger.error("Report generation failed", e);
        }
        return report;
    }
    
    public Report generateInventoryReport() {
        Report report = new Report();
        List<InventoryItem> items = inventory.getAllItems();
        for (InventoryItem item : items) {
            report.addLine(item.getName() + ": " + item.getQuantity());
        }
        return report;
    }
    
    // Validation
    public boolean validateOrder(Order order) {
        if (order.getItems() == null || order.getItems().isEmpty()) {
            logger.error("Order has no items");
            return false;
        }
        for (OrderItem item : order.getItems()) {
            if (item.getQuantity() <= 0) {
                logger.error("Invalid quantity for item: " + item.getProductId());
                return false;
            }
        }
        return true;
    }
    
    public boolean validatePayment(Payment payment) {
        if (payment.getAmount() <= 0) {
            return false;
        }
        if (payment.getCardNumber() == null || payment.getCardNumber().length() < 13) {
            return false;
        }
        return true;
    }
    
    // Database operations
    public void connectDatabase(String url, String username, String password) {
        try {
            database = java.sql.DriverManager.getConnection(url, username, password);
            logger.log("Database connected");
        } catch (Exception e) {
            logger.error("Database connection failed", e);
        }
    }
    
    public void closeDatabase() {
        try {
            if (database != null) {
                database.close();
            }
        } catch (Exception e) {
            logger.error("Database close failed", e);
        }
    }
    
    // Helper methods
    private void saveToDatabase(Order order) throws Exception {
        // Implementation
    }
    
    private void updateInventory(Order order) {
        // Implementation
    }
    
    private void updateOrderStatus(String orderId, String status) {
        // Implementation
    }
    
    private Payment findPayment(String paymentId) {
        // Implementation
        return null;
    }
}

// Supporting classes
class Order {
    private String id;
    private String customerId;
    private String customerEmail;
    private String status;
    private List<OrderItem> items;
    
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getCustomerId() { return customerId; }
    public void setCustomerId(String customerId) { this.customerId = customerId; }
    public String getCustomerEmail() { return customerEmail; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public List<OrderItem> getItems() { return items; }
}

class OrderItem {
    private String productId;
    private int quantity;
    
    public String getProductId() { return productId; }
    public int getQuantity() { return quantity; }
}

class Payment {
    private String id;
    private String orderId;
    private String customerId;
    private String customerEmail;
    private String cardNumber;
    private double amount;
    
    public String getId() { return id; }
    public String getOrderId() { return orderId; }
    public String getCustomerId() { return customerId; }
    public String getCustomerEmail() { return customerEmail; }
    public String getCardNumber() { return cardNumber; }
    public double getAmount() { return amount; }
}

class Report {
    private String title;
    private double totalSales;
    private List<String> lines;
    
    public Report() {
        this.lines = new ArrayList<>();
    }
    
    public void setTitle(String title) { this.title = title; }
    public void setTotalSales(double total) { this.totalSales = total; }
    public void addLine(String line) { this.lines.add(line); }
}

class EmailService {
    public void send(String to, String subject, String message) {}
}

class Logger {
    public Logger(String name) {}
    public void log(String message) {}
    public void error(String message) {}
    public void error(String message, Exception e) {}
    public void warn(String message) {}
}

class PaymentGateway {
    public boolean charge(Payment payment) { return true; }
    public void refund(Payment payment) {}
}

class InventorySystem {
    public List<InventoryItem> getAllItems() { return new ArrayList<>(); }
}

class InventoryItem {
    private String name;
    private int quantity;
    
    public String getName() { return name; }
    public int getQuantity() { return quantity; }
}

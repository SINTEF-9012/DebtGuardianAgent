package com.example.samples;

import java.util.List;
import java.util.ArrayList;

/**
 * Examples of Long Method and Feature Envy code smells
 */
public class CodeSmellExamples {
    
    /**
     * LONG METHOD - This method does too much and should be split
     */
    public void processOrder(Order order) {
        // Validation
        if (order == null) {
            System.err.println("Order is null");
            return;
        }
        if (order.getItems().isEmpty()) {
            System.err.println("Order has no items");
            return;
        }
        
        // Calculate totals
        double subtotal = 0.0;
        for (OrderItem item : order.getItems()) {
            if (item.getQuantity() <= 0) {
                System.err.println("Invalid quantity for item: " + item.getProductId());
                continue;
            }
            double itemTotal = item.getPrice() * item.getQuantity();
            subtotal += itemTotal;
        }
        
        // Apply discounts
        double discount = 0.0;
        if (order.getCustomer().isPremium()) {
            discount = subtotal * 0.1;
        }
        if (subtotal > 100) {
            discount += 10.0;
        }
        
        // Calculate tax
        double taxRate = 0.08;
        String state = order.getCustomer().getAddress().getState();
        if (state.equals("CA")) {
            taxRate = 0.0725;
        } else if (state.equals("NY")) {
            taxRate = 0.04;
        } else if (state.equals("TX")) {
            taxRate = 0.0625;
        }
        double tax = (subtotal - discount) * taxRate;
        
        // Final total
        double total = subtotal - discount + tax;
        order.setTotal(total);
        
        // Update inventory
        for (OrderItem item : order.getItems()) {
            Inventory inventory = getInventory();
            Product product = inventory.findProduct(item.getProductId());
            if (product != null) {
                int newQuantity = product.getQuantity() - item.getQuantity();
                product.setQuantity(newQuantity);
                inventory.updateProduct(product);
            }
        }
        
        // Save to database
        try {
            Database db = getDatabase();
            db.save(order);
            System.out.println("Order saved: " + order.getId());
        } catch (Exception e) {
            System.err.println("Failed to save order: " + e.getMessage());
            throw new RuntimeException("Order processing failed");
        }
        
        // Send confirmation
        EmailService emailService = getEmailService();
        String customerEmail = order.getCustomer().getEmail();
        String message = buildConfirmationEmail(order);
        emailService.sendEmail(customerEmail, "Order Confirmation", message);
        
        // Log activity
        Logger logger = getLogger();
        logger.log("Order processed: " + order.getId());
        logger.log("Customer: " + order.getCustomer().getName());
        logger.log("Total: $" + total);
    }
    
    /**
     * FEATURE ENVY - This method is too dependent on Customer class
     */
    public String generateCustomerReport(Customer customer) {
        StringBuilder report = new StringBuilder();
        report.append("Customer Report\n");
        report.append("================\n\n");
        
        report.append("Name: ").append(customer.getFirstName())
              .append(" ").append(customer.getLastName()).append("\n");
        report.append("Email: ").append(customer.getEmail()).append("\n");
        report.append("Phone: ").append(customer.getPhone()).append("\n");
        
        Address address = customer.getAddress();
        report.append("Address: ").append(address.getStreet()).append(", ");
        report.append(address.getCity()).append(", ");
        report.append(address.getState()).append(" ");
        report.append(address.getZipCode()).append("\n\n");
        
        report.append("Account Status: ");
        if (customer.isPremium()) {
            report.append("Premium Member\n");
            report.append("Member Since: ").append(customer.getMemberSince()).append("\n");
        } else {
            report.append("Standard Member\n");
        }
        
        report.append("\nOrder History:\n");
        int orderCount = 0;
        double totalSpent = 0.0;
        for (Order order : customer.getOrders()) {
            orderCount++;
            totalSpent += order.getTotal();
            report.append("  Order #").append(order.getId());
            report.append(" - Date: ").append(order.getDate());
            report.append(" - Amount: $").append(order.getTotal()).append("\n");
            
            for (OrderItem item : order.getItems()) {
                report.append("    - ").append(item.getProductName());
                report.append(" (").append(item.getQuantity()).append(")");
                report.append(" - $").append(item.getPrice()).append("\n");
            }
        }
        
        report.append("\nSummary:\n");
        report.append("Total Orders: ").append(orderCount).append("\n");
        report.append("Total Spent: $").append(totalSpent).append("\n");
        
        if (totalSpent > 1000) {
            report.append("VIP Customer - High Value!\n");
        }
        
        return report.toString();
    }
    
    /**
     * Another FEATURE ENVY example
     */
    public void updateCustomerLoyaltyPoints(Customer customer) {
        int currentPoints = customer.getLoyaltyPoints();
        int newPoints = 0;
        
        for (Order order : customer.getOrders()) {
            if (order.getDate().after(getLastMonthDate())) {
                newPoints += (int)(order.getTotal() / 10);
            }
        }
        
        customer.setLoyaltyPoints(currentPoints + newPoints);
        
        if (customer.getLoyaltyPoints() > 1000 && !customer.isPremium()) {
            customer.setPremium(true);
            customer.setMemberSince(new java.util.Date());
            sendPremiumUpgradeEmail(customer.getEmail());
        }
    }
    
    // Helper methods
    private Database getDatabase() { return null; }
    private Inventory getInventory() { return null; }
    private EmailService getEmailService() { return null; }
    private Logger getLogger() { return null; }
    private java.util.Date getLastMonthDate() { return null; }
    private void sendPremiumUpgradeEmail(String email) {}
    private String buildConfirmationEmail(Order order) { return ""; }
}

// Supporting classes
class Customer {
    private String id;
    private String firstName;
    private String lastName;
    private String email;
    private String phone;
    private Address address;
    private boolean premium;
    private java.util.Date memberSince;
    private int loyaltyPoints;
    private List<Order> orders;
    
    public String getId() { return id; }
    public String getFirstName() { return firstName; }
    public String getLastName() { return lastName; }
    public String getName() { return firstName + " " + lastName; }
    public String getEmail() { return email; }
    public String getPhone() { return phone; }
    public Address getAddress() { return address; }
    public boolean isPremium() { return premium; }
    public void setPremium(boolean premium) { this.premium = premium; }
    public java.util.Date getMemberSince() { return memberSince; }
    public void setMemberSince(java.util.Date date) { this.memberSince = date; }
    public int getLoyaltyPoints() { return loyaltyPoints; }
    public void setLoyaltyPoints(int points) { this.loyaltyPoints = points; }
    public List<Order> getOrders() { return orders != null ? orders : new ArrayList<>(); }
}

class Address {
    private String street;
    private String city;
    private String state;
    private String zipCode;
    
    public String getStreet() { return street; }
    public String getCity() { return city; }
    public String getState() { return state; }
    public String getZipCode() { return zipCode; }
}

class Order {
    private String id;
    private Customer customer;
    private List<OrderItem> items;
    private double total;
    private java.util.Date date;
    
    public String getId() { return id; }
    public Customer getCustomer() { return customer; }
    public List<OrderItem> getItems() { return items != null ? items : new ArrayList<>(); }
    public double getTotal() { return total; }
    public void setTotal(double total) { this.total = total; }
    public java.util.Date getDate() { return date; }
}

class OrderItem {
    private String productId;
    private String productName;
    private int quantity;
    private double price;
    
    public String getProductId() { return productId; }
    public String getProductName() { return productName; }
    public int getQuantity() { return quantity; }
    public double getPrice() { return price; }
}

class Product {
    private String id;
    private int quantity;
    
    public int getQuantity() { return quantity; }
    public void setQuantity(int quantity) { this.quantity = quantity; }
}

class Database {
    public void save(Order order) throws Exception {}
}

class Inventory {
    public Product findProduct(String id) { return null; }
    public void updateProduct(Product product) {}
}

class EmailService {
    public void sendEmail(String to, String subject, String message) {}
}

class Logger {
    public void log(String message) {}
}

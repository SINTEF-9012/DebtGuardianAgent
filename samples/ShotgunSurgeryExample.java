package com.example.samples;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

/** PricingRule and dependant domain classes */

// --- PricingRule ---

class PricingRule {
    private String ruleId;
    private String ruleType;    // "flat", "percentage", "tiered"
    private double baseRate;
    private Map<String, Double> tierRates;
    private boolean applyToSubtotal;
    private String currency;

    public PricingRule(String ruleId, String ruleType, double baseRate) {
        this.ruleId = ruleId;
        this.ruleType = ruleType;
        this.baseRate = baseRate;
        this.tierRates = new HashMap<>();
        this.applyToSubtotal = true;
        this.currency = "USD";
    }

    public String getRuleId() { return ruleId; }
    public String getRuleType() { return ruleType; }
    public double getBaseRate() { return baseRate; }
    public Map<String, Double> getTierRates() { return tierRates; }
    public boolean isApplyToSubtotal() { return applyToSubtotal; }
    public String getCurrency() { return currency; }

    public double computeAdjustment(double amount) {
        switch (ruleType) {
            case "flat":
                return baseRate;
            case "percentage":
                return amount * baseRate;
            case "tiered":
                return computeTieredAdjustment(amount);
            default:
                return 0.0;
        }
    }

    private double computeTieredAdjustment(double amount) {
        double adjustment = 0;
        for (Map.Entry<String, Double> tier : tierRates.entrySet()) {
            double threshold = Double.parseDouble(tier.getKey());
            if (amount >= threshold) {
                adjustment = tier.getValue() * amount;
            }
        }
        return adjustment;
    }
}


// --- OrderService ---

class OrderService {
    private List<PricingRule> applicableRules;

    public double calculateTotal(List<LineItem> items) {
        double subtotal = 0;
        for (LineItem item : items) {
            subtotal += item.getPrice() * item.getQuantity();
        }

        double discount = 0;
        for (PricingRule rule : applicableRules) {
            if (rule.isApplyToSubtotal()) {
                discount += rule.computeAdjustment(subtotal);
            } else {
                // Apply per-item
                for (LineItem item : items) {
                    discount += rule.computeAdjustment(item.getPrice());
                }
            }
        }

        return subtotal - discount;
    }
}

// --- InvoiceService ---

class InvoiceService {
    public String generateInvoice(Order order, List<PricingRule> rules) {
        StringBuilder invoice = new StringBuilder();
        invoice.append("Invoice for Order: ").append(order.getId()).append("\n");

        for (PricingRule rule : rules) {
            invoice.append("Applied rule: ").append(rule.getRuleId());
            invoice.append(" (").append(rule.getRuleType()).append(")");
            invoice.append(" rate=").append(rule.getBaseRate());
            invoice.append(" currency=").append(rule.getCurrency()).append("\n");
        }

        return invoice.toString();
    }
}

// --- DiscountEngine ---

class DiscountEngine {
    private List<PricingRule> allRules;

    public List<PricingRule> selectApplicableRules(String customerTier, double orderAmount) {
        List<PricingRule> applicable = new ArrayList<>();

        for (PricingRule rule : allRules) {
            // Decision logic tightly coupled to PricingRule's internal ruleType values
            if (rule.getRuleType().equals("percentage") && orderAmount > 100) {
                applicable.add(rule);
            } else if (rule.getRuleType().equals("tiered") && !rule.getTierRates().isEmpty()) {
                applicable.add(rule);
            } else if (rule.getRuleType().equals("flat")) {
                applicable.add(rule);
            }
        }

        return applicable;
    }
}

// --- TaxCalculator ---

class TaxCalculator {
    private double taxRate;

    public TaxCalculator(double taxRate) {
        this.taxRate = taxRate;
    }

    public double computeTax(double subtotal, List<PricingRule> discountRules) {
        double afterDiscount = subtotal;

        for (PricingRule rule : discountRules) {
            double adjustment = rule.computeAdjustment(afterDiscount);
            if (rule.getRuleType().equals("flat")) {
                afterDiscount -= adjustment;
            } else {
                afterDiscount -= adjustment;
            }
        }

        return afterDiscount * taxRate;
    }
}

// --- QuoteGenerator ---

class QuoteGenerator {
    public String buildQuote(List<LineItem> items, List<PricingRule> rules) {
        StringBuilder quote = new StringBuilder();
        quote.append("Price Quote\n");
        quote.append("===========\n");

        double subtotal = 0;
        for (LineItem item : items) {
            subtotal += item.getPrice() * item.getQuantity();
        }

        quote.append("Subtotal: ").append(subtotal).append("\n");

        for (PricingRule rule : rules) {
            double adj = rule.computeAdjustment(subtotal);
            quote.append("Rule ").append(rule.getRuleId());
            quote.append(" (").append(rule.getRuleType()).append("): -");
            quote.append(adj).append(" ").append(rule.getCurrency()).append("\n");
        }

        return quote.toString();
    }
}

// --- BillingService ---

class BillingService {
    public double processBilling(Customer customer, List<PricingRule> rules) {
        double baseCharge = customer.getSubscriptionAmount();

        for (PricingRule rule : rules) {
            if (rule.isApplyToSubtotal()) {
                double discount = rule.computeAdjustment(baseCharge);
                baseCharge -= discount;
            }
        }

        // Log the applied pricing
        for (PricingRule rule : rules) {
            System.out.println("Applied " + rule.getRuleType() + " rule " +
                             rule.getRuleId() + " with rate " + rule.getBaseRate());
        }

        return baseCharge;
    }
}


// --- Supporting classes ---

class LineItem {
    private String productId;
    private double price;
    private int quantity;

    public String getProductId() { return productId; }
    public double getPrice() { return price; }
    public int getQuantity() { return quantity; }
}

class Order {
    private String id;
    private List<LineItem> items;

    public String getId() { return id; }
    public List<LineItem> getItems() { return items; }
}

class Customer {
    private String name;
    private double subscriptionAmount;

    public String getName() { return name; }
    public double getSubscriptionAmount() { return subscriptionAmount; }
}

using System;
using System.Collections.Generic;

/// <summary>
/// SHOTGUN SURGERY - Example of a class whose changes ripple across many others.
///
/// When PricingRule changes (e.g., adding a new pricing tier or changing the
/// computation), at least 6 other domain classes must be modified in tandem.
///
/// This is NOT just high fan-in (like a Logger or utility class). Each dependent
/// class uses PricingRule's internal structure (RuleType, BaseRate, TierRates) in
/// domain-specific ways. A change to PricingRule's design would require touching
/// every one of them — the hallmark of Shotgun Surgery.
/// </summary>

// ============================================================================
// The problematic class — changes here force changes in 6+ other classes
// ============================================================================

public class PricingRule
{
    public string RuleId { get; }
    public string RuleType { get; }      // "flat", "percentage", "tiered"
    public double BaseRate { get; }
    public Dictionary<string, double> TierRates { get; }
    public bool ApplyToSubtotal { get; }
    public string Currency { get; }

    public PricingRule(string ruleId, string ruleType, double baseRate)
    {
        RuleId = ruleId;
        RuleType = ruleType;
        BaseRate = baseRate;
        TierRates = new Dictionary<string, double>();
        ApplyToSubtotal = true;
        Currency = "USD";
    }

    public double ComputeAdjustment(double amount)
    {
        return RuleType switch
        {
            "flat"       => BaseRate,
            "percentage" => amount * BaseRate,
            "tiered"     => ComputeTieredAdjustment(amount),
            _            => 0.0
        };
    }

    private double ComputeTieredAdjustment(double amount)
    {
        double adjustment = 0;
        foreach (var tier in TierRates)
        {
            double threshold = double.Parse(tier.Key);
            if (amount >= threshold)
            {
                adjustment = tier.Value * amount;
            }
        }
        return adjustment;
    }
}


// ============================================================================
// Dependent class 1: OrderService inspects PricingRule internals
// ============================================================================

public class OrderService
{
    private List<PricingRule> applicableRules;

    public double CalculateTotal(List<LineItem> items)
    {
        double subtotal = 0;
        foreach (var item in items)
        {
            subtotal += item.Price * item.Quantity;
        }

        double discount = 0;
        foreach (var rule in applicableRules)
        {
            if (rule.ApplyToSubtotal)
            {
                discount += rule.ComputeAdjustment(subtotal);
            }
            else
            {
                foreach (var item in items)
                {
                    discount += rule.ComputeAdjustment(item.Price);
                }
            }
        }

        return subtotal - discount;
    }
}

// ============================================================================
// Dependent class 2: InvoiceService formats pricing details
// ============================================================================

public class InvoiceService
{
    public string GenerateInvoice(Order order, List<PricingRule> rules)
    {
        var invoice = new System.Text.StringBuilder();
        invoice.AppendLine($"Invoice for Order: {order.Id}");

        foreach (var rule in rules)
        {
            invoice.AppendLine(
                $"Applied rule: {rule.RuleId} ({rule.RuleType}) rate={rule.BaseRate} currency={rule.Currency}");
        }

        return invoice.ToString();
    }
}

// ============================================================================
// Dependent class 3: DiscountEngine selects applicable rules
// ============================================================================

public class DiscountEngine
{
    private List<PricingRule> allRules;

    public List<PricingRule> SelectApplicableRules(string customerTier, double orderAmount)
    {
        var applicable = new List<PricingRule>();

        foreach (var rule in allRules)
        {
            // Decision logic tightly coupled to PricingRule's internal RuleType values
            if (rule.RuleType == "percentage" && orderAmount > 100)
                applicable.Add(rule);
            else if (rule.RuleType == "tiered" && rule.TierRates.Count > 0)
                applicable.Add(rule);
            else if (rule.RuleType == "flat")
                applicable.Add(rule);
        }

        return applicable;
    }
}

// ============================================================================
// Dependent class 4: TaxCalculator applies rules before tax
// ============================================================================

public class TaxCalculator
{
    private readonly double _taxRate;

    public TaxCalculator(double taxRate) { _taxRate = taxRate; }

    public double ComputeTax(double subtotal, List<PricingRule> discountRules)
    {
        double afterDiscount = subtotal;

        foreach (var rule in discountRules)
        {
            double adjustment = rule.ComputeAdjustment(afterDiscount);
            afterDiscount -= adjustment;
        }

        return afterDiscount * _taxRate;
    }
}

// ============================================================================
// Dependent class 5: QuoteGenerator previews pricing for customers
// ============================================================================

public class QuoteGenerator
{
    public string BuildQuote(List<LineItem> items, List<PricingRule> rules)
    {
        var quote = new System.Text.StringBuilder();
        quote.AppendLine("Price Quote");
        quote.AppendLine("===========");

        double subtotal = 0;
        foreach (var item in items)
        {
            subtotal += item.Price * item.Quantity;
        }

        quote.AppendLine($"Subtotal: {subtotal}");

        foreach (var rule in rules)
        {
            double adj = rule.ComputeAdjustment(subtotal);
            quote.AppendLine($"Rule {rule.RuleId} ({rule.RuleType}): -{adj} {rule.Currency}");
        }

        return quote.ToString();
    }
}

// ============================================================================
// Dependent class 6: BillingService processes recurring billing with pricing rules
// ============================================================================

public class BillingService
{
    public double ProcessBilling(Customer customer, List<PricingRule> rules)
    {
        double baseCharge = customer.SubscriptionAmount;

        foreach (var rule in rules)
        {
            if (rule.ApplyToSubtotal)
            {
                double discount = rule.ComputeAdjustment(baseCharge);
                baseCharge -= discount;
            }
        }

        // Log the applied pricing
        foreach (var rule in rules)
        {
            Console.WriteLine(
                $"Applied {rule.RuleType} rule {rule.RuleId} with rate {rule.BaseRate}");
        }

        return baseCharge;
    }
}


// ============================================================================
// Supporting classes
// ============================================================================

public class LineItem
{
    public string ProductId { get; set; }
    public double Price { get; set; }
    public int Quantity { get; set; }
}

public class Order
{
    public string Id { get; set; }
    public List<LineItem> Items { get; set; }
}

public class Customer
{
    public string Name { get; set; }
    public double SubscriptionAmount { get; set; }
}

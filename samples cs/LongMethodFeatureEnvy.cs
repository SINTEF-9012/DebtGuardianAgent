using System;
using System.Collections.Generic;
using System.Text;

public class CodeSmellExamples
{
    public void ProcessOrder(Order order)
    {
        // Validation
        if (order == null)
        {
            Console.Error.WriteLine("Order is null");
            return;
        }
        if (order.Items == null || order.Items.Count == 0)
        {
            Console.Error.WriteLine("Order has no items");
            return;
        }

        // Calculate totals
        double subtotal = 0.0;
        foreach (var item in order.Items)
        {
            if (item.Quantity <= 0)
            {
                Console.Error.WriteLine("Invalid quantity for item: " + item.ProductId);
                continue;
            }
            double itemTotal = item.Price * item.Quantity;
            subtotal += itemTotal;
        }

        // Apply discounts
        double discount = 0.0;
        if (order.Customer.IsPremium)
        {
            discount = subtotal * 0.1;
        }
        if (subtotal > 100)
        {
            discount += 10.0;
        }

        // Calculate tax
        double taxRate = 0.08;
        string state = order.Customer.Address.State;
        if (state == "CA")
        {
            taxRate = 0.0725;
        }
        else if (state == "NY")
        {
            taxRate = 0.04;
        }
        else if (state == "TX")
        {
            taxRate = 0.0625;
        }
        double tax = (subtotal - discount) * taxRate;

        // Final total
        double total = subtotal - discount + tax;
        order.Total = total;

        // Update inventory
        foreach (var item in order.Items)
        {
            Inventory inventory = GetInventory();
            Product product = inventory.FindProduct(item.ProductId);
            if (product != null)
            {
                int newQuantity = product.Quantity - item.Quantity;
                product.Quantity = newQuantity;
                inventory.UpdateProduct(product);
            }
        }

        // Save to database
        try
        {
            Database db = GetDatabase();
            db.Save(order);
            Console.WriteLine("Order saved: " + order.Id);
        }
        catch (Exception e)
        {
            Console.Error.WriteLine("Failed to save order: " + e.Message);
            throw new InvalidOperationException("Order processing failed");
        }

        // Send confirmation
        EmailService emailService = GetEmailService();
        string customerEmail = order.Customer.Email;
        string message = BuildConfirmationEmail(order);
        emailService.SendEmail(customerEmail, "Order Confirmation", message);

        // Log activity
        AppLogger logger = GetLogger();
        logger.Log("Order processed: " + order.Id);
        logger.Log("Customer: " + order.Customer.Name);
        logger.Log("Total: $" + total);
    }

    public string GenerateCustomerReport(Customer customer)
    {
        var report = new StringBuilder();
        report.AppendLine("Customer Report");
        report.AppendLine("================\n");

        report.Append("Name: ").Append(customer.FirstName)
              .Append(" ").AppendLine(customer.LastName);
        report.Append("Email: ").AppendLine(customer.Email);
        report.Append("Phone: ").AppendLine(customer.Phone);

        Address address = customer.Address;
        report.Append("Address: ").Append(address.Street).Append(", ");
        report.Append(address.City).Append(", ");
        report.Append(address.State).Append(" ");
        report.AppendLine(address.ZipCode);

        report.Append("Account Status: ");
        if (customer.IsPremium)
        {
            report.AppendLine("Premium Member");
            report.Append("Member Since: ").AppendLine(customer.MemberSince.ToString());
        }
        else
        {
            report.AppendLine("Standard Member");
        }

        report.AppendLine("\nOrder History:");
        int orderCount = 0;
        double totalSpent = 0.0;
        foreach (var order in customer.Orders)
        {
            orderCount++;
            totalSpent += order.Total;
            report.Append("  Order #").Append(order.Id);
            report.Append(" - Date: ").Append(order.Date);
            report.Append(" - Amount: $").AppendLine(order.Total.ToString());

            foreach (var item in order.Items)
            {
                report.Append("    - ").Append(item.ProductName);
                report.Append(" (").Append(item.Quantity).Append(")");
                report.Append(" - $").AppendLine(item.Price.ToString());
            }
        }

        report.AppendLine("\nSummary:");
        report.Append("Total Orders: ").AppendLine(orderCount.ToString());
        report.Append("Total Spent: $").AppendLine(totalSpent.ToString());

        if (totalSpent > 1000)
        {
            report.AppendLine("VIP Customer - High Value!");
        }

        return report.ToString();
    }

    public void UpdateCustomerLoyaltyPoints(Customer customer)
    {
        int currentPoints = customer.LoyaltyPoints;
        int newPoints = 0;

        foreach (var order in customer.Orders)
        {
            if (order.Date > GetLastMonthDate())
            {
                newPoints += (int)(order.Total / 10);
            }
        }

        customer.LoyaltyPoints = currentPoints + newPoints;

        if (customer.LoyaltyPoints > 1000 && !customer.IsPremium)
        {
            customer.IsPremium = true;
            customer.MemberSince = DateTime.Now;
            SendPremiumUpgradeEmail(customer.Email);
        }
    }

    // Helper methods
    private Database GetDatabase() { return null; }
    private Inventory GetInventory() { return null; }
    private EmailService GetEmailService() { return null; }
    private AppLogger GetLogger() { return null; }
    private DateTime GetLastMonthDate() { return DateTime.Now.AddMonths(-1); }
    private void SendPremiumUpgradeEmail(string email) { }
    private string BuildConfirmationEmail(Order order) { return ""; }
}

// Supporting classes
class Customer
{
    public string Id { get; set; }
    public string FirstName { get; set; }
    public string LastName { get; set; }
    public string Name => FirstName + " " + LastName;
    public string Email { get; set; }
    public string Phone { get; set; }
    public Address Address { get; set; }
    public bool IsPremium { get; set; }
    public DateTime MemberSince { get; set; }
    public int LoyaltyPoints { get; set; }
    public List<Order> Orders { get; set; } = new List<Order>();
}

class Address
{
    public string Street { get; set; }
    public string City { get; set; }
    public string State { get; set; }
    public string ZipCode { get; set; }
}

class Order
{
    public string Id { get; set; }
    public Customer Customer { get; set; }
    public List<OrderItem> Items { get; set; } = new List<OrderItem>();
    public double Total { get; set; }
    public DateTime Date { get; set; }
}

class OrderItem
{
    public string ProductId { get; set; }
    public string ProductName { get; set; }
    public int Quantity { get; set; }
    public double Price { get; set; }
}

class Product
{
    public string Id { get; set; }
    public int Quantity { get; set; }
}

class Database
{
    public void Save(Order order) { }
}

class Inventory
{
    public Product FindProduct(string id) { return null; }
    public void UpdateProduct(Product product) { }
}

class EmailService
{
    public void SendEmail(string to, string subject, string message) { }
}

class AppLogger
{
    public void Log(string message) { }
}

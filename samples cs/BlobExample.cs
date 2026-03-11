using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SqlClient;

/// <summary>
/// OrderManager - Example of Blob (God Class) code smell
/// This class has too many responsibilities and should be split
/// </summary>
public class OrderManager
{
    private SqlConnection database;
    private EmailService emailService;
    private AppLogger logger;
    private PaymentGateway paymentGateway;
    private InventorySystem inventory;
    private Dictionary<string, Order> orderCache;

    public OrderManager()
    {
        this.orderCache = new Dictionary<string, Order>();
        this.logger = new AppLogger("OrderManager");
    }

    // Order CRUD operations
    public void CreateOrder(Order order)
    {
        try
        {
            ValidateOrder(order);
            SaveToDatabase(order);
            UpdateInventory(order);
            SendOrderConfirmation(order);
            orderCache[order.Id] = order;
            logger.Log("Order created: " + order.Id);
        }
        catch (Exception e)
        {
            logger.Error("Failed to create order", e);
        }
    }

    public void UpdateOrder(Order order)
    {
        if (!orderCache.ContainsKey(order.Id))
        {
            logger.Warn("Order not in cache: " + order.Id);
        }
        try
        {
            var cmd = database.CreateCommand();
            cmd.CommandText = "UPDATE orders SET status='" + order.Status +
                              "' WHERE id='" + order.Id + "'";
            cmd.ExecuteNonQuery();
            orderCache[order.Id] = order;
        }
        catch (Exception e)
        {
            logger.Error("Update failed", e);
        }
    }

    public void DeleteOrder(string orderId)
    {
        try
        {
            var cmd = database.CreateCommand();
            cmd.CommandText = "DELETE FROM orders WHERE id='" + orderId + "'";
            cmd.ExecuteNonQuery();
            orderCache.Remove(orderId);
            logger.Log("Order deleted: " + orderId);
        }
        catch (Exception e)
        {
            logger.Error("Delete failed", e);
        }
    }

    public List<Order> FindOrders(string criteria)
    {
        var results = new List<Order>();
        try
        {
            var cmd = database.CreateCommand();
            cmd.CommandText = "SELECT * FROM orders WHERE " + criteria;
            using (var reader = cmd.ExecuteReader())
            {
                while (reader.Read())
                {
                    var order = new Order();
                    order.Id = reader["id"].ToString();
                    order.CustomerId = reader["customer_id"].ToString();
                    order.Status = reader["status"].ToString();
                    results.Add(order);
                }
            }
        }
        catch (Exception e)
        {
            logger.Error("Find failed", e);
        }
        return results;
    }

    // Payment processing
    public bool ProcessPayment(Payment payment)
    {
        try
        {
            if (payment.Amount <= 0)
            {
                return false;
            }
            bool result = paymentGateway.Charge(payment);
            if (result)
            {
                UpdateOrderStatus(payment.OrderId, "PAID");
                SendPaymentConfirmation(payment);
            }
            return result;
        }
        catch (Exception e)
        {
            logger.Error("Payment processing failed", e);
            return false;
        }
    }

    public void RefundPayment(string paymentId)
    {
        try
        {
            Payment payment = FindPayment(paymentId);
            paymentGateway.Refund(payment);
            UpdateOrderStatus(payment.OrderId, "REFUNDED");
            SendRefundNotification(payment);
        }
        catch (Exception e)
        {
            logger.Error("Refund failed", e);
        }
    }

    // Notification handling
    public void SendOrderConfirmation(Order order)
    {
        string message = "Your order " + order.Id + " has been confirmed.";
        emailService.Send(order.CustomerEmail, "Order Confirmation", message);
    }

    public void SendShippingNotification(Order order)
    {
        string message = "Your order " + order.Id + " has been shipped.";
        emailService.Send(order.CustomerEmail, "Shipping Update", message);
    }

    public void SendPaymentConfirmation(Payment payment)
    {
        string message = "Payment received: $" + payment.Amount;
        emailService.Send(payment.CustomerEmail, "Payment Confirmation", message);
    }

    public void SendRefundNotification(Payment payment)
    {
        string message = "Refund processed: $" + payment.Amount;
        emailService.Send(payment.CustomerEmail, "Refund Processed", message);
    }

    // Reporting
    public Report GenerateSalesReport(string startDate, string endDate)
    {
        var report = new Report();
        try
        {
            var cmd = database.CreateCommand();
            cmd.CommandText =
                "SELECT SUM(amount) as total FROM orders WHERE date BETWEEN '" +
                startDate + "' AND '" + endDate + "'";
            using (var reader = cmd.ExecuteReader())
            {
                if (reader.Read())
                {
                    report.TotalSales = Convert.ToDouble(reader["total"]);
                }
            }
            report.Title = "Sales Report: " + startDate + " to " + endDate;
        }
        catch (Exception e)
        {
            logger.Error("Report generation failed", e);
        }
        return report;
    }

    public Report GenerateInventoryReport()
    {
        var report = new Report();
        List<InventoryItem> items = inventory.GetAllItems();
        foreach (var item in items)
        {
            report.AddLine(item.Name + ": " + item.Quantity);
        }
        return report;
    }

    // Validation
    public bool ValidateOrder(Order order)
    {
        if (order.Items == null || order.Items.Count == 0)
        {
            logger.Error("Order has no items");
            return false;
        }
        foreach (var item in order.Items)
        {
            if (item.Quantity <= 0)
            {
                logger.Error("Invalid quantity for item: " + item.ProductId);
                return false;
            }
        }
        return true;
    }

    public bool ValidatePayment(Payment payment)
    {
        if (payment.Amount <= 0)
            return false;
        if (string.IsNullOrEmpty(payment.CardNumber) || payment.CardNumber.Length < 13)
            return false;
        return true;
    }

    // Database operations
    public void ConnectDatabase(string connectionString)
    {
        try
        {
            database = new SqlConnection(connectionString);
            database.Open();
            logger.Log("Database connected");
        }
        catch (Exception e)
        {
            logger.Error("Database connection failed", e);
        }
    }

    public void CloseDatabase()
    {
        try
        {
            database?.Close();
        }
        catch (Exception e)
        {
            logger.Error("Database close failed", e);
        }
    }

    // Helper methods
    private void SaveToDatabase(Order order) { }
    private void UpdateInventory(Order order) { }
    private void UpdateOrderStatus(string orderId, string status) { }
    private Payment FindPayment(string paymentId) { return null; }
}

// Supporting classes
class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }
    public string CustomerEmail { get; set; }
    public string Status { get; set; }
    public List<OrderItem> Items { get; set; }
}

class OrderItem
{
    public string ProductId { get; set; }
    public int Quantity { get; set; }
}

class Payment
{
    public string Id { get; set; }
    public string OrderId { get; set; }
    public string CustomerId { get; set; }
    public string CustomerEmail { get; set; }
    public string CardNumber { get; set; }
    public double Amount { get; set; }
}

class Report
{
    private List<string> lines = new List<string>();

    public string Title { get; set; }
    public double TotalSales { get; set; }
    public void AddLine(string line) { lines.Add(line); }
}

class EmailService
{
    public void Send(string to, string subject, string message) { }
}

class AppLogger
{
    public AppLogger(string name) { }
    public void Log(string message) { }
    public void Error(string message) { }
    public void Error(string message, Exception e) { }
    public void Warn(string message) { }
}

class PaymentGateway
{
    public bool Charge(Payment payment) { return true; }
    public void Refund(Payment payment) { }
}

class InventorySystem
{
    public List<InventoryItem> GetAllItems() { return new List<InventoryItem>(); }
}

class InventoryItem
{
    public string Name { get; set; }
    public int Quantity { get; set; }
}

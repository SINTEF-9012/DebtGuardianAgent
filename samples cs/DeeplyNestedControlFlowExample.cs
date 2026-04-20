using System;
using System.Collections.Generic;

namespace DebtGuardianSamples
{
    public class OrderProcessor
    {
        public void ProcessOrder(Order order)
        {
            if (order != null)
            {
                if (order.IsValid())
                {
                    if (order.Items != null && order.Items.Count > 0)
                    {
                        foreach (var item in order.Items)
                        {
                            if (item != null)
                            {
                                if (item.InStock)
                                {
                                    if (item.Quantity > 0)
                                    {
                                        if (order.Customer != null)
                                        {
                                            if (order.Customer.IsActive)
                                            {
                                                if (order.Payment != null)
                                                {
                                                    if (order.Payment.IsAuthorized)
                                                    {
                                                        if (order.ShippingAddress != null)
                                                        {
                                                            if (order.ShippingAddress.IsValid())
                                                            {
                                                                Console.WriteLine("Processing item: " + item.Name);
                                                            }
                                                            else
                                                            {
                                                                Console.WriteLine("Invalid shipping address");
                                                            }
                                                        }
                                                        else
                                                        {
                                                            Console.WriteLine("Missing shipping address");
                                                        }
                                                    }
                                                    else
                                                    {
                                                        Console.WriteLine("Payment not authorized");
                                                    }
                                                }
                                                else
                                                {
                                                    Console.WriteLine("Missing payment info");
                                                }
                                            }
                                            else
                                            {
                                                Console.WriteLine("Inactive customer");
                                            }
                                        }
                                        else
                                        {
                                            Console.WriteLine("No customer info");
                                        }
                                    }
                                    else
                                    {
                                        Console.WriteLine("Invalid quantity");
                                    }
                                }
                                else
                                {
                                    Console.WriteLine("Item out of stock");
                                }
                            }
                        }
                    }
                    else
                    {
                        Console.WriteLine("No items in order");
                    }
                }
                else
                {
                    Console.WriteLine("Invalid order");
                }
            }
            else
            {
                Console.WriteLine("Order is null");
            }
        }
    }

    // Supporting classes
    public class Order
    {
        public List<OrderItem> Items { get; set; }
        public Customer Customer { get; set; }
        public Payment Payment { get; set; }
        public Address ShippingAddress { get; set; }

        public bool IsValid() => true;
    }

    public class OrderItem
    {
        public string Name { get; set; }
        public bool InStock { get; set; }
        public int Quantity { get; set; }
    }

    public class Customer
    {
        public bool IsActive { get; set; }
    }

    public class Payment
    {
        public bool IsAuthorized { get; set; }
    }

    public class Address
    {
        public bool IsValid() => true;
    }
}
using System;

/// <summary>
/// CustomerRecord — stores customer profile data
/// </summary>
public class CustomerRecord
{
    public string Id { get; set; }
    public string FirstName { get; set; }
    public string LastName { get; set; }
    public string Email { get; set; }
    public string Phone { get; set; }
    public string Address { get; set; }
    public string City { get; set; }
    public string State { get; set; }
    public string ZipCode { get; set; }
    public string Country { get; set; }
    public bool Active { get; set; }
    public DateTime CreatedDate { get; set; }
    public DateTime LastModified { get; set; }

    public CustomerRecord() { }

    public CustomerRecord(string id, string firstName, string lastName, string email)
    {
        Id = id;
        FirstName = firstName;
        LastName = lastName;
        Email = email;
        Active = true;
        CreatedDate = DateTime.Now;
    }
}


/// <summary>
/// ProductDTO — product catalogue entry
/// </summary>
public class ProductDTO
{
    public string ProductId { get; set; }
    public string Name { get; set; }
    public string Description { get; set; }
    public double Price { get; set; }
    public int StockQuantity { get; set; }
    public string Category { get; set; }
    public string Manufacturer { get; set; }
    public double Weight { get; set; }
    public string Dimensions { get; set; }
}

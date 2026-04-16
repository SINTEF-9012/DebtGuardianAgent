class CodeSmellExamples {

    processOrder(order) {
        // Validation
        if (!order) {
            console.error("Order is null");
            return;
        }
        if (!order.items || order.items.length === 0) {
            console.error("Order has no items");
            return;
        }

        // Calculate totals
        let subtotal = 0;
        for (const item of order.items) {
            if (item.quantity <= 0) {
                console.error("Invalid quantity for item: " + item.productId);
                continue;
            }
            subtotal += item.price * item.quantity;
        }

        // Apply discounts
        let discount = 0;
        if (order.customer.premium) {
            discount = subtotal * 0.1;
        }
        if (subtotal > 100) {
            discount += 10.0;
        }

        // Calculate tax
        let taxRate = 0.08;
        const state = order.customer.address.state;
        if (state === "CA") {
            taxRate = 0.0725;
        } else if (state === "NY") {
            taxRate = 0.04;
        } else if (state === "TX") {
            taxRate = 0.0625;
        }
        const tax = (subtotal - discount) * taxRate;

        // Final total
        const total = subtotal - discount + tax;
        order.total = total;

        // Update inventory
        for (const item of order.items) {
            const inventory = this.getInventory();
            const product = inventory.findProduct(item.productId);
            if (product) {
                product.quantity -= item.quantity;
                inventory.updateProduct(product);
            }
        }

        // Save to database
        try {
            const db = this.getDatabase();
            db.save(order);
            console.log("Order saved: " + order.id);
        } catch (e) {
            console.error("Failed to save order: " + e.message);
            throw new Error("Order processing failed");
        }

        // Send confirmation
        const emailService = this.getEmailService();
        emailService.sendEmail(
            order.customer.email,
            "Order Confirmation",
            this.buildConfirmationEmail(order)
        );

        // Log activity
        console.log("Order processed: " + order.id);
        console.log("Customer: " + order.customer.firstName + " " + order.customer.lastName);
        console.log("Total: $" + total);
    }

    generateCustomerReport(customer) {
        let report = "";
        report += "Customer Report\n";
        report += "================\n\n";

        report += "Name: " + customer.firstName + " " + customer.lastName + "\n";
        report += "Email: " + customer.email + "\n";
        report += "Phone: " + customer.phone + "\n";

        const address = customer.address;
        report += "Address: " + address.street + ", ";
        report += address.city + ", ";
        report += address.state + " ";
        report += address.zipCode + "\n\n";

        report += "Account Status: ";
        if (customer.premium) {
            report += "Premium Member\n";
            report += "Member Since: " + customer.memberSince + "\n";
        } else {
            report += "Standard Member\n";
        }

        report += "\nOrder History:\n";
        let orderCount = 0;
        let totalSpent = 0;
        for (const order of customer.orders) {
            orderCount++;
            totalSpent += order.total;
            report += "  Order #" + order.id;
            report += " - Date: " + order.date;
            report += " - Amount: $" + order.total + "\n";

            for (const item of order.items) {
                report += "    - " + item.productName;
                report += " (" + item.quantity + ")";
                report += " - $" + item.price + "\n";
            }
        }

        report += "\nSummary:\n";
        report += "Total Orders: " + orderCount + "\n";
        report += "Total Spent: $" + totalSpent + "\n";

        if (totalSpent > 1000) {
            report += "VIP Customer - High Value!\n";
        }

        return report;
    }

    updateCustomerLoyaltyPoints(customer) {
        let currentPoints = customer.loyaltyPoints;
        let newPoints = 0;

        const lastMonth = new Date();
        lastMonth.setMonth(lastMonth.getMonth() - 1);

        for (const order of customer.orders) {
            if (new Date(order.date) > lastMonth) {
                newPoints += Math.floor(order.total / 10);
            }
        }

        customer.loyaltyPoints = currentPoints + newPoints;

        if (customer.loyaltyPoints > 1000 && !customer.premium) {
            customer.premium = true;
            customer.memberSince = new Date();
            this.sendPremiumUpgradeEmail(customer.email);
        }
    }

    // Helper methods
    getDatabase() { return null; }
    getInventory() { return null; }
    getEmailService() { return null; }
    sendPremiumUpgradeEmail(email) {}
    buildConfirmationEmail(order) { return ""; }
}

module.exports = { CodeSmellExamples };

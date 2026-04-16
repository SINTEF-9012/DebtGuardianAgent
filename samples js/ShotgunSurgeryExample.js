/** PricingRule and dependant classes */

class PricingRule {
    constructor(name, discountPercentage, minQuantity, applicableCategory, startDate, endDate) {
        this.name = name;
        this.discountPercentage = discountPercentage;
        this.minQuantity = minQuantity;
        this.applicableCategory = applicableCategory;
        this.startDate = startDate;
        this.endDate = endDate;
    }
}


// --- Classes that reference PricingRule ---

class PricingRuleValidator {
    validate(rule) {
        if (!rule.name || rule.name.trim().length === 0) return false;
        if (rule.discountPercentage < 0 || rule.discountPercentage > 100) return false;
        if (rule.minQuantity < 0) return false;
        if (rule.startDate && rule.endDate && rule.startDate > rule.endDate) return false;
        return true;
    }
}


class PricingRuleFormatter {
    formatForDisplay(rule) {
        let sb = "Rule: " + rule.name + "\n";
        sb += "  Discount: " + rule.discountPercentage + "%\n";
        sb += "  Min Quantity: " + rule.minQuantity + "\n";
        sb += "  Category: " + rule.applicableCategory + "\n";
        if (rule.startDate) {
            sb += "  Active: " + rule.startDate.toISOString().slice(0, 10)
                + " to " + rule.endDate.toISOString().slice(0, 10) + "\n";
        }
        return sb;
    }
}


class PricingRuleRepository {
    constructor() {
        this.database = null;
    }

    save(rule) {
        const sql = "INSERT INTO pricing_rules "
            + "(name, discount_percentage, min_quantity, applicable_category, start_date, end_date) "
            + "VALUES ('"
            + rule.name + "', "
            + rule.discountPercentage + ", "
            + rule.minQuantity + ", '"
            + rule.applicableCategory + "', '"
            + rule.startDate + "', '"
            + rule.endDate + "')";
        this.database.query(sql);
    }

    findByCategory(category) {
        return this.database.query(
            "SELECT name, discount_percentage, min_quantity FROM pricing_rules "
            + "WHERE applicable_category = '" + category + "'"
        );
    }
}


class PricingRuleEngine {
    applyRule(rule, item) {
        if (item.category !== rule.applicableCategory) return item.price;
        if (item.quantity < rule.minQuantity) return item.price;

        const now = new Date();
        if (rule.startDate && now < rule.startDate) return item.price;
        if (rule.endDate && now > rule.endDate) return item.price;

        return item.price * (1 - rule.discountPercentage / 100);
    }
}


class PricingRuleImporter {
    importFromJSON(json) {
        const data = JSON.parse(json);
        const rules = [];
        for (const entry of data) {
            rules.push(new PricingRule(
                entry.name,
                entry.discountPercentage,
                entry.minQuantity,
                entry.applicableCategory,
                entry.startDate ? new Date(entry.startDate) : null,
                entry.endDate   ? new Date(entry.endDate)   : null
            ));
        }
        return rules;
    }
}


class PricingRuleAuditLogger {
    logChange(oldRule, newRule) {
        const changes = [];
        if (oldRule.name !== newRule.name)
            changes.push("name: " + oldRule.name + " -> " + newRule.name);
        if (oldRule.discountPercentage !== newRule.discountPercentage)
            changes.push("discount: " + oldRule.discountPercentage + " -> " + newRule.discountPercentage);
        if (oldRule.minQuantity !== newRule.minQuantity)
            changes.push("minQty: " + oldRule.minQuantity + " -> " + newRule.minQuantity);
        if (oldRule.applicableCategory !== newRule.applicableCategory)
            changes.push("category: " + oldRule.applicableCategory + " -> " + newRule.applicableCategory);

        console.log("PricingRule changes: " + changes.join(", "));
    }
}

module.exports = {
    PricingRule,
    PricingRuleValidator,
    PricingRuleFormatter,
    PricingRuleRepository,
    PricingRuleEngine,
    PricingRuleImporter,
    PricingRuleAuditLogger,
};

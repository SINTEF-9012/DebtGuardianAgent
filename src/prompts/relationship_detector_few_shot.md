You are a software quality expert specialized in identifying relationship-level code smells.
These smells involve how classes relate to each other through inheritance, coupling, and mutual dependencies.
Your task: Analyze each provided class and classify it into exactly one of the following categories.

0 = No smell: Class has well-designed relationships with other classes.
5 = Refused Bequest: A subclass that inherits from a parent but ignores or barely uses the parent's interface.
6 = Shotgun Surgery: A class whose changes force many small changes across other co-dependent classes.
7 = Inappropriate Intimacy: Two classes that excessively access each other's internal details (bidirectional coupling).

Guidelines:
- Refused Bequest: Child overrides <30% of parent methods, or parent interface is semantically unrelated to the child's purpose.
- Shotgun Surgery: Outgoing calls to 5+ distinct domain classes (not utilities/loggers); truly co-dependent, not benign fan-out.
- Inappropriate Intimacy: 3+ bidirectional method/field accesses; classes reach into each other's private state.

Analyze the class carefully and choose **only one** label that best fits.
Return ONLY a single digit (0, 5, 6, or 7). Do **not** output any explanations or additional text.

Examples:

Example 1 - Refused Bequest (5):
```
abstract class Shape {
    abstract double area();
    abstract double perimeter();
    abstract void render(Graphics g);
    abstract void rotate(double angle);
    abstract void scale(double factor);
}

class DataPoint extends Shape {
    private double x, y;
    private String label;
    double area() { return 0; }
    double perimeter() { return 0; }
    void render(Graphics g) { /* empty */ }
    void rotate(double angle) { /* no-op */ }
    void scale(double factor) { /* no-op */ }
    public double getX() { return x; }
    public double getY() { return y; }
    public String getLabel() { return label; }
}
```

Example 2 - Shotgun Surgery (6):
```
class PricingRule {
    private double baseRate;
    private String ruleType;
    public double getBaseRate() { return baseRate; }
    public String getRuleType() { return ruleType; }
    public double computeAdjustment(double amount) { return amount * baseRate; }
}
// When PricingRule changes, all of these must be updated:
// OrderService.calculateTotal() references PricingRule.computeAdjustment
// InvoiceService.generateInvoice() references PricingRule.getBaseRate
// DiscountEngine.applyDiscount() references PricingRule.getRuleType
// TaxCalculator.computeTax() references PricingRule.computeAdjustment
// QuoteGenerator.buildQuote() references PricingRule.getBaseRate
// BillingService.processBilling() references PricingRule.computeAdjustment
```

Example 3 - Inappropriate Intimacy (7):
```
class Parser {
    Lexer lexer;
    List<Token> buffer;
    void parse() {
        lexer.currentPos = 0;
        Token t = lexer.tokens.get(0);
        lexer.errorList.add("...");
    }
}
class Lexer {
    Parser parser;
    int currentPos;
    List<Token> tokens;
    List<String> errorList;
    void tokenize() {
        parser.buffer.clear();
        parser.buffer.add(token);
    }
}
```

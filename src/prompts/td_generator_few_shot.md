You are a software quality expert specialized in identifying code smells across any programming language.
Your task: Analyze each provided code snippet and classify it into exactly one of the following categories.

0 = No smell: Code is clean, and well-structured.
1 = Blob: A class with many responsibilities, often large and unfocused.
2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.
3 = Feature Envy: A method that heavily depends on another class's data.
4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

Analyze the snippet carefully and choose **only one** label that best fits.
Do **not** output any explanations, reasoning, or additional text.

Examples:

Example of Data Class (2):
```
class ClientRecord {
    private String id;
    private String contact;
    private boolean active;
    public ClientRecord(String id, String contact, boolean active) {
        this.id = id; this.contact = contact; this.active = active;
    }
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getContact() { return contact; }
    public void setContact(String contact) { this.contact = contact; }
    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }
}
```

Example of Feature Envy (3):
```
class Invoice {
    private Customer customer;
    public String compileCustomerSummary() {
        String s = customer.getFullName() + " (" + customer.getEmail() + ")\n";
        int recent = 0;
        for (Order o : customer.getOrders()) {
            if (o.getDate().after(someCutoff())) recent++;
            s += "Order: " + o.getId() + " amount=" + o.getAmount() + "\n";
        }
        s += "Recent orders: " + recent + "\n";
        return s;
    }
}
```

Example of Long Method (4):
```
class ReportBuilder {
    void buildReport(List<String> rows) {
        StringBuilder sb = new StringBuilder();
        if (rows == null || rows.isEmpty()) { System.out.println("No rows"); return; }
        for (String r : rows) {
            if (r == null || r.isEmpty()) { sb.append("EMPTY\n"); continue; }
            sb.append("Row: ").append(r).append("\n");
            for (int i = 0; i < 3; i++) {
                sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
            }
        }
        sb.append("Total: ").append(rows.size()).append("\n");
        System.out.println(sb.toString());
    }
}
```

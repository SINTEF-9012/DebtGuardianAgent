import configparser
import os
import sys

# ========================================================================================
# DIRECTORY CONFIGURATION
# ========================================================================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
LOG_DIR = os.path.join(ROOT_DIR, 'logs')
RESULT_DIR = os.path.join(ROOT_DIR, 'results')
WORK_DIR = os.path.join(ROOT_DIR, "work")
REPO_DIR = os.path.join(ROOT_DIR, "repositories")

# Create directories if they don't exist
for directory in [DATA_DIR, RESULT_DIR, WORK_DIR, REPO_DIR]:
    os.makedirs(directory, exist_ok=True)
    sys.path.append(directory)

# ========================================================================================
# LLM CONFIGURATION
# ========================================================================================

LLM_SERVICE = "ollama"
LLM_MODEL = "qwen3:4b-instruct" 
LLM_MODEL_CLASS = "codestral:latest" 
LLM_MODEL_METHOD = "qwen2.5:7b-instruct" 
TEMPERATURE = 0.0

LLM_CONFIG = {
    "cache_seed": None,
    "config_list": [
        {
            "model": LLM_MODEL,
            "api_base": "http://localhost:11434",
            "api_type": LLM_SERVICE,
            "num_ctx": 262144,
        }
    ],
    "temperature": TEMPERATURE
}

# Base LLM config for Ollama (local models)
LLM_CONFIG_OLLAMA = {
    "config_list": [
        {
            "model": "qwen2.5-coder:7b",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
        }
    ],
    "temperature": 0.1,
    "timeout": 600,
    "cache_seed": None,
}


config = configparser.ConfigParser()
PATH_CONFIG = os.path.join(ROOT_DIR, 'config.ini')
config.read(PATH_CONFIG)

# Extract API keys
#openai_engine_name = config['OPENAI']['engine_name']
#openai_api_key = config['OPENAI']['api_key']
#openai_api_type = config['OPENAI']['api_type']
#openai_api_base = config['OPENAI']['api_base']
#openai_api_version = config['OPENAI']['api_version']

#neptune_api_token = config['NEPTUNE']['api_token']

#model_type = None
#repo_url = None


IN_FILE = "mlcq_cleaned_and_pruned_dataset_385.csv"
GT_FILE = "mlcq_cleaned_and_pruned_dataset_385.csv"

# ========================================================================================
# AGENT-SPECIFIC MODEL CONFIGURATION
# ========================================================================================
AGENT_CONFIGS = {
    'source_loader': {
        'enabled': True,
    },
    'program_slicer': {
        'enabled': True,
        'extract_metrics': True,
        'min_method_loc': 3,  # Minimum lines for method to be analyzed
        'max_class_loc': 2000,  # Maximum class size to analyze
    },
    'class_detector': {
        'model': 'codestral:22b',
        'base_url': 'http://localhost:11434',
        'api_key': 'ollama',
        'shot': 'few',
        'timeout': 300,
        'temperature': 0.1,
        'enabled': True,
    },
    'method_detector': {
        'model': 'qwen2.5-coder:7b',
        'base_url': 'http://localhost:11434',
        'api_key': 'ollama',
        'shot': 'zero',
        'timeout': 300,
        'temperature': 0.1,
        'enabled': True,
    },
    'localization': {
        'enabled': True,
        'use_ast': True,  # Use AST parsing for precise localization
    },
    'explanation': {
        'model': 'codestral:22b',
        'base_url': 'http://localhost:11434',
        'api_key': 'ollama',
        'temperature': 0.1,
        'max_tokens': 1000,
        'enabled': True,
    },
    'fix_suggestion': {
        'model': 'codestral:22b',
        'base_url': 'http://localhost:11434',
        'api_key': 'ollama',
        'temperature': 0.1,
        'max_tokens': 2000,
        'enabled': False,  # Can be expensive, enable when needed
        'validate_fixes': False,
    },
    'coordinator': {
        'parallel_detection': True,
        'conflict_resolution_strategy': 'prioritize_class',  # or 'keep_all', 'prioritize_method'
        'min_confidence': 0.5,  # Filter results below this confidence
    }
}

# ========================================================================================
# PIPELINE CONFIGURATION
# ========================================================================================
PIPELINE_CONFIG = {
    'parallel_detection': True,
    'enable_localization': True,
    'enable_explanation': True,
    'enable_fix_suggestion': False,
    'batch_size': 10,  # Process files in batches
    'max_workers': 4,  # For parallel processing
}

# ========================================================================================
# TECHNICAL DEBT CATEGORIES
# ========================================================================================
TD_CATEGORIES = {
    0: {
        'name': 'No Smell',
        'granularity': 'any',
        'severity': 'none',
        'description': 'Code is clean and well-structured'
    },
    1: {
        'name': 'Blob',
        'granularity': 'class',
        'severity': 'high',
        'description': 'Class with too many responsibilities (God Class)'
    },
    2: {
        'name': 'Data Class',
        'granularity': 'class',
        'severity': 'medium',
        'description': 'Class with only getters/setters, no behavior'
    },
    3: {
        'name': 'Feature Envy',
        'granularity': 'method',
        'severity': 'medium',
        'description': 'Method heavily dependent on another class'
    },
    4: {
        'name': 'Long Method',
        'granularity': 'method',
        'severity': 'high',
        'description': 'Excessively long or complex method'
    },
}


# Thresholds for heuristic-based detection assistance
THRESHOLDS = {
    'blob_class_loc': 500,
    'blob_method_count': 20,
    'long_method_loc': 20,
    'long_method_complexity': 10,
    'data_class_method_ratio': 0.8,  # Ratio of getters/setters to total methods
}

SUPPORTED_EXTENSIONS = {
    'java': '.java',
    'cpp': '.cpp',
    'cs': '.cs',
    'python': '.py',
    'javascript': '.js'
}

# ========================================================================================
# PROMPTS FOR CLASS-LEVEL DEBT DETECTION
# ========================================================================================
SYS_MSG_CLASS_DETECTOR_FEW_SHOT = """
    You are a software quality expert specialized in identifying class-level code smells in Java code.
    Your task: Analyze each provided Java class and classify it into exactly one of the following categories.

    0 = No smell: Class is clean and well-structured.
    1 = Blob: A class with many responsibilities, often large and unfocused (God Class).
    2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.

    Guidelines:
    - Blob: Look for classes with 15+ methods, multiple unrelated responsibilities, or exceeding 300 LOC
    - Data Class: Look for classes where `>70%` of methods are getters/setters with minimal business logic

    Analyze the class carefully and choose **only one** label that best fits.
    Return ONLY a single digit (0, 1, or 2). Do **not** output any explanations or additional text.

    Examples:

    Example 1 - Data Class (2):
    ```java
    class CustomerRecord {
        private String id;
        private String name;
        private String email;
        private String phone;
        
        public CustomerRecord(String id, String name, String email, String phone) {
            this.id = id;
            this.name = name;
            this.email = email;
            this.phone = phone;
        }
        
        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getEmail() { return email; }
        public void setEmail(String email) { this.email = email; }
        public String getPhone() { return phone; }
        public void setPhone(String phone) { this.phone = phone; }
    }
    ```

    Example 2 - Blob (1):
    ```java
    class OrderManager {
        private Database db;
        private EmailService emailService;
        private Logger logger;
        private PaymentGateway paymentGateway;
        
        // Order management
        public void createOrder(Order o) { /*...*/ }
        public void updateOrder(Order o) { /*...*/ }
        public void deleteOrder(String id) { /*...*/ }
        public List<Order> findOrders(String criteria) { /*...*/ }
        
        // Payment processing
        public boolean processPayment(Payment p) { /*...*/ }
        public void refundPayment(String id) { /*...*/ }
        
        // Notification
        public void sendOrderConfirmation(Order o) { /*...*/ }
        public void sendShippingNotification(Order o) { /*...*/ }
        
        // Reporting
        public Report generateSalesReport() { /*...*/ }
        public Report generateInventoryReport() { /*...*/ }
        
        // Validation
        public boolean validateOrder(Order o) { /*...*/ }
        public boolean validatePayment(Payment p) { /*...*/ }
        
        // Database operations
        public void connectDatabase() { /*...*/ }
        public void closeDatabase() { /*...*/ }
    }
    ```
"""

SYS_MSG_CLASS_DETECTOR_ZERO_SHOT = """
    You are a software quality expert specialized in identifying class-level code smells in Java code.
    Your task: Analyze each provided Java class and classify it into exactly one of the following categories.

    0 = No smell: Class is clean and well-structured.
    1 = Blob: A class with many responsibilities, often large and unfocused (God Class).
    2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.

    Guidelines:
    - Blob: Look for classes with 15+ methods, multiple unrelated responsibilities, or exceeding 300 LOC
    - Data Class: Look for classes where `>70%` of methods are getters/setters with minimal business logic

    Analyze the class carefully and choose **only one** label that best fits.
    Return ONLY a single digit (0, 1, or 2). Do **not** output any explanations or additional text.
"""

# ========================================================================================
# PROMPTS FOR METHOD-LEVEL DEBT DETECTION
# ========================================================================================
SYS_MSG_METHOD_DETECTOR_FEW_SHOT = """
    You are a software quality expert specialized in identifying method-level code smells in Java code.
    Your task: Analyze each provided Java method and classify it into exactly one of the following categories.

    0 = No smell: Method is clean and well-structured.
    3 = Feature Envy: A method that heavily depends on another class's data more than its own.
    4 = Long Method: A method that is excessively long or complex (typically >=15 executable lines).

    Guidelines:
    - Feature Envy: Method makes 5+ calls to another class's getters/methods, or builds strings/logic primarily from external data
    - Long Method: Method has 15+ lines of executable code (excluding comments/braces), high cyclomatic complexity, or multiple nested loops

    Analyze the method carefully and choose **only one** label that best fits.
    Return ONLY a single digit (0, 3, or 4). Do **not** output any explanations or additional text.

    Examples:

    Example 1 - Feature Envy (3):
    ```java
    public String generateCustomerReport(Customer customer) {
        StringBuilder report = new StringBuilder();
        report.append("Customer: ").append(customer.getFullName()).append("\n");
        report.append("Email: ").append(customer.getEmail()).append("\n");
        report.append("Phone: ").append(customer.getPhone()).append("\n");
        report.append("Address: ").append(customer.getAddress()).append("\n");
        
        int orderCount = 0;
        double totalSpent = 0.0;
        for (Order order : customer.getOrders()) {
            orderCount++;
            totalSpent += order.getAmount();
            report.append("Order ").append(order.getId()).append(": $").append(order.getAmount()).append("\n");
        }
        
        report.append("Total Orders: ").append(orderCount).append("\n");
        report.append("Total Spent: $").append(totalSpent).append("\n");
        return report.toString();
    }
    ```

    Example 2 - Long Method (4):
    ```java
    public void processOrder(Order order) {
        // Validation
        if (order == null) {
            logger.error("Order is null");
            return;
        }
        if (order.getItems().isEmpty()) {
            logger.error("Order has no items");
            return;
        }
        
        // Calculate totals
        double subtotal = 0.0;
        for (OrderItem item : order.getItems()) {
            if (item.getQuantity() <= 0) {
                logger.warn("Invalid quantity for item: " + item.getProductId());
                continue;
            }
            double itemTotal = item.getPrice() * item.getQuantity();
            subtotal += itemTotal;
        }
        
        // Apply discounts
        double discount = 0.0;
        if (order.getCustomer().isPremium()) {
            discount = subtotal * 0.1;
        }
        if (subtotal > 100) {
            discount += 10.0;
        }
        
        // Calculate tax
        double taxRate = 0.08;
        double tax = (subtotal - discount) * taxRate;
        
        // Final total
        double total = subtotal - discount + tax;
        order.setTotal(total);
        
        // Save to database
        try {
            database.save(order);
            logger.info("Order saved: " + order.getId());
        } catch (Exception e) {
            logger.error("Failed to save order: " + e.getMessage());
            throw new RuntimeException("Order processing failed");
        }
        
        // Send confirmation
        emailService.sendOrderConfirmation(order);
    }
    ```
"""

SYS_MSG_METHOD_DETECTOR_ZERO_SHOT = """
    You are a software quality expert specialized in identifying method-level code smells in Java code.
    Your task: Analyze each provided Java method and classify it into exactly one of the following categories.

    0 = No smell: Method is clean and well-structured.
    3 = Feature Envy: A method that heavily depends on another class's data more than its own.
    4 = Long Method: A method that is excessively long or complex (typically >=15 executable lines).

    Guidelines:
    - Feature Envy: Method makes 5+ calls to another class's getters/methods, or builds strings/logic primarily from external data
    - Long Method: Method has 15+ lines of executable code (excluding comments/braces), high cyclomatic complexity, or multiple nested loops

    Analyze the method carefully and choose **only one** label that best fits.
    Return ONLY a single digit (0, 3, or 4). Do **not** output any explanations or additional text.

"""

TASK_PROMPT_CLASS_DETECTION = """Analyze the following Java class and respond with only a single digit (0, 1, or 2) representing the code smell category:\n\n"""

TASK_PROMPT_METHOD_DETECTION = """Analyze the following Java method and respond with only a single digit (0, 3, or 4) representing the code smell category:\n\n"""

# ========================================================================================
# PROMPTS FOR EXPLANATION AGENT
# ========================================================================================
SYS_MSG_EXPLANATION_AGENT = """
    You are a software quality expert who explains code smells to developers in a clear, constructive manner.

    Your task: Given a detected code smell, explain:
    1. WHY it is considered technical debt (what symptoms make it problematic)
    2. CONSEQUENCES of leaving it unaddressed (maintenance issues, bugs, complexity growth)
    3. IMPACT on code quality metrics (readability, maintainability, testability)

    Keep explanations concise (3-5 sentences), developer-friendly, and actionable.
    Focus on helping developers understand the issue without being preachy.
"""

# ========================================================================================
# PROMPTS FOR FIX SUGGESTION AGENT
# ========================================================================================
SYS_MSG_FIX_SUGGESTION_AGENT = """
    You are a software refactoring expert who provides practical, actionable fix suggestions.

    Your task: Given a code smell, suggest specific refactoring steps:
    1. Identify the refactoring pattern to apply (Extract Method, Move Method, etc.)
    2. Provide concrete steps to refactor the code
    3. Show a brief code example of the improved structure (if appropriate)

    Keep suggestions practical and focused on the most impactful improvements.
    Consider the effort required vs. benefit gained.
"""



# ========================================================================================
# TECHNICAL DEBT DETECTION CONFIGURATION_OLD
# ========================================================================================
TASK_PROMPT_TD_DETECTION = """Look at the following Java code snippet and respond with only a single digit (0-4) that represents the most appropriate category:\n"""

# System messages (separate for class- and method-level agents)
SYS_MSG_CLASS_LEVEL_FEW = """
You are a software quality expert specialized in identifying class-level code smells in Java.
Your task: Given a Java class snippet, classify it into exactly one of the following categories.
0 = No smell: class is well-structured and focused.
1 = Blob: A class with many responsibilities, often large and unfocused.
2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.

Return **only** a single digit (0,1,2) — no explanations or extra text.
"""


SYS_MSG_METHOD_LEVEL_FEW = """
You are a software quality expert specialized in identifying method-level code smells in Java.
Your task: Given a Java method snippet, classify it into exactly one of the following categories.
0 = No smell: Method is concise and cohesive.
3 = Feature Envy: A method that heavily depends on another class's data.
4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).


Return **only** a single digit (3,4,0) — no explanations or extra text.
"""


# File extensions we consider
SOURCE_FILE_EXTS = [".java"]


SYS_MSG_TD_DETECTION_GENERATOR_FEW_SHOT ="""
        You are a software quality expert specialized in identifying code smells in Java code snippets.
        Your task: Analyze each provided Java code snippet and classify it into exactly one of the following categories.
        0 = No smell: Code is clean, and well-structured.
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Analyze the snippet carefully and choose **only one** label that best fits.
        Do **not** output any explanations, reasoning, or additional text.

        Here are a few examples of code snippets and the types of code smells they contain:
        Example of Data Class ('2'):
            class ClientRecord {
                private String id;
                private String contact;
                private boolean active;
                public ClientRecord(String id, String contact, boolean active) {
                    this.id = id;
                    this.contact = contact;
                    this.active = active;
                }
                public String getId() { return id; }
                public void setId(String id) { this.id = id; }
                public String getContact() { return contact; }
                public void setContact(String contact) { this.contact = contact; }
                public boolean isActive() { return active; }
                public void setActive(boolean active) { this.active = active; }
            }

        Example of Feature Envy ('3'):
            public class ReportPrinter {
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

        Example of Long Method ('4'):
            class ReportBuilder {
                void buildReport(List<String> rows) {
                    StringBuilder sb = new StringBuilder();

                    // Validate
                    if (rows == null || rows.isEmpty()) {
                        System.out.println("No rows to process");
                        return;
                    }

                    // Process rows
                    for (String r : rows) {
                        if (r == null || r.isEmpty()) {
                            sb.append("EMPTY\n");
                            continue;
                        }
                        sb.append("Row: ").append(r).append("\n");

                        for (int i = 0; i < 3; i++) {
                            sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
                        }
                    }

                    // Aggregate
                    sb.append("Total: ").append(rows.size()).append("\n");
                    System.out.println(sb.toString());
                }
            }
        """

SYS_MSG_TD_DETECTION_GENERATOR_ZERO_SHOT ="""
        You are a software quality expert specialized in identifying code smells in Java code snippets.
        Your task: Analyze each provided Java code snippet and classify it into exactly one of the following categories.
        0 = No smell: Code is clean, and well-structured.
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that primarily contains fields with getters/setters but lacks meaningful behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Analyze the snippet carefully and choose **only one** label that best fits.
        Do **not** output any explanations, reasoning, or additional text.
        """


SYS_MSG_TD_DETECTION_CRITIC_ZERO_SHOT = """
        You are a software quality critic. Your task is to verify or correct the code smell label assigned to a Java code snippet by another agent.
        You will be given:
        1) The Java code snippet itself
        2) A proposed label produced by the td_detection_generator_agent (a single digit 0-4)

        Labels:
        0 = No smell: Code is clean and well-structured
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that only stores fields with getters/setters and no behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Task:
        - Review the snippet and verify whether the proposed label is correct.
        - If the proposed label is correct, respond with exactly:
                APPROVED|<correct_digit>|
            (nothing else, single token, uppercase).
        - If the proposed label is incorrect, respond with exactly one single-line string in this format:
                REJECTED|<correct_digit>|<brief_reason>
            where:
            * <correct_digit> is the correct label (0-4).
            * <brief_reason> is a concise 1-2 short-sentence justification (max 25 words) that explains the primary evidence for the correction.
            Use '|' (pipe) as separators and do not include any other characters, lines, or commentary.

        Examples of valid critic outputs:
        APPROVED|2|
        REJECTED|2|Class only has fields and trivial getters/setters, no behavior.

        Constraints:
        - Do not output anything other than the exact allowed formats above.
        - Keep the brief_reason factual, focused, and short (one or two clauses).
        """

SYS_MSG_TD_DETECTION_CRITIC_FEW_SHOT = """
        You are a software quality critic. Your task is to verify or correct the code smell label assigned to a Java code snippet by another agent.
        You will be given:
        1) The Java code snippet itself
        2) A proposed label produced by the td_detection_generator_agent (a single digit 0-4)
        
        Labels:
        0 = No smell: Code is clean and well-structured
        1 = Blob: A class with many responsibilities, often large and unfocused.
        2 = Data Class: A class that only stores fields with getters/setters and no behavior.
        3 = Feature Envy: A method that heavily depends on another class's data.
        4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

        Task:
        - Review the snippet and verify whether the proposed label is correct.
        - If the proposed label is correct, respond with exactly:
                APPROVED|<correct_digit>|
            (nothing else, single token, uppercase).
        - If the proposed label is incorrect, respond with exactly one single-line string in this format:
                REJECTED|<correct_digit>|<brief_reason>
            where:
            * <correct_digit> is the correct label (0-4).
            * <brief_reason> is a concise 1-2 short-sentence justification (max ~25 words) that explains the primary evidence for the correction.
            Use '|' (pipe) as separators and do not include any other characters, lines, or commentary.

        Examples of valid critic outputs:
        APPROVED|2|
        REJECTED|2|Class only has fields and trivial getters/setters, no behavior.

        Constraints:
        - Do not output anything other than the exact allowed formats above.
        - Keep the brief_reason factual, focused, and short (one or two clauses).

        Here are a few examples of code snippets and the types of code smells they contain:
        Example of Data Class (2):
            class ClientRecord {
                private String id;
                private String contact;
                private boolean active;
                public ClientRecord(String id, String contact, boolean active) {
                    this.id = id;
                    this.contact = contact;
                    this.active = active;
                }
                public String getId() { return id; }
                public void setId(String id) { this.id = id; }
                public String getContact() { return contact; }
                public void setContact(String contact) { this.contact = contact; }
                public boolean isActive() { return active; }
                public void setActive(boolean active) { this.active = active; }
            }

        Example of Feature Envy (3):
            public class ReportPrinter {
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

        Example of Long Method (4):
            class ReportBuilder {
                void buildReport(List<String> rows) {
                    StringBuilder sb = new StringBuilder();

                    // Validate
                    if (rows == null || rows.isEmpty()) {
                        System.out.println("No rows to process");
                        return;
                    }

                    // Process rows
                    for (String r : rows) {
                        if (r == null || r.isEmpty()) {
                            sb.append("EMPTY\n");
                            continue;
                        }
                        sb.append("Row: ").append(r).append("\n");

                        for (int i = 0; i < 3; i++) {
                            sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
                        }
                    }

                    // Aggregate
                    sb.append("Total: ").append(rows.size()).append("\n");
                    System.out.println(sb.toString());
                }
            }
        """

SYS_MSG_TD_DETECTION_REFINER_ZERO_SHOT = """
    You are a software quality refiner. You will be given three inputs:
    - CODE_SNIPPET: a Java code snippet
    - GENERATOR_LABEL: a single digit (0-4) from the td_detection_generator_agent
    - CRITIC_LABEL: a single digit (0-4) from the td_detection_critic_agent

    Labels:
    0 = No smell: Code is clean and well-structured
    1 = Blob: A class with many responsibilities, often large and unfocused.
    2 = Data Class: A class that only stores fields with getters/setters and no behavior.
    3 = Feature Envy: A method that heavily depends on another class's data.
    4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

    Task:
    - Analyze the CODE_SNIPPET yourself and determine the most accurate label (0-4).
    - Use GENERATOR_LABEL and CRITIC_LABEL as references; if both are reasonable, prefer the critic's label.
    - Always output exactly one digit (0-4) and nothing else — no explanations, punctuation, or extra text.
    """


SYS_MSG_TD_DETECTION_REFINER_FEW_SHOT = """
    You are a software quality refiner. You will be given three inputs:
    - CODE_SNIPPET: a Java code snippet
    - GENERATOR_LABEL: a single digit (0-4) from the td_detection_generator_agent
    - CRITIC_LABEL: a single digit (0-4) from the td_detection_critic_agent

    Labels:
    0 = No smell: Code is clean and well-structured
    1 = Blob: A class with many responsibilities, often large and unfocused.
    2 = Data Class: A class that only stores fields with getters/setters and no behavior.
    3 = Feature Envy: A method that heavily depends on another class's data.
    4 = Long Method: A method that is excessively long or complex (typically >=8-20 executable lines).

    Task:
    - Analyze the CODE_SNIPPET yourself and determine the most accurate label (0-4).
    - Use GENERATOR_LABEL and CRITIC_LABEL as references; if both are reasonable, prefer the critic's label.
    - Always output exactly one digit (0-4) and nothing else — no explanations, punctuation, or extra text.

    Here are a few examples of code snippets and the types of code smells they contain:
    Example of Data Class (2):
        class ClientRecord {
            private String id;
            private String contact;
            private boolean active;
            public ClientRecord(String id, String contact, boolean active) {
                this.id = id;
                this.contact = contact;
                this.active = active;
            }
            public String getId() { return id; }
            public void setId(String id) { this.id = id; }
            public String getContact() { return contact; }
            public void setContact(String contact) { this.contact = contact; }
            public boolean isActive() { return active; }
            public void setActive(boolean active) { this.active = active; }
        }

    Example of Feature Envy (3):
        public class ReportPrinter {
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

    Example of Long Method (4):
        class ReportBuilder {
            void buildReport(List<String> rows) {
                StringBuilder sb = new StringBuilder();

                // Validate
                if (rows == null || rows.isEmpty()) {
                    System.out.println("No rows to process");
                    return;
                }

                // Process rows
                for (String r : rows) {
                    if (r == null || r.isEmpty()) {
                        sb.append("EMPTY\n");
                        continue;
                    }
                    sb.append("Row: ").append(r).append("\n");

                    for (int i = 0; i < 3; i++) {
                        sb.append("Pass ").append(i).append(" for ").append(r).append("\n");
                    }
                }

                // Aggregate
                sb.append("Total: ").append(rows.size()).append("\n");
                System.out.println(sb.toString());
            }
        }
    """


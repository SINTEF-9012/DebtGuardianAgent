# 🧠 DebtGuardianAgent
> An LLM-powered multi-agent system for detecting Technical Debt in real-world software repositories.

---

## 📌 Overview

Technical Debt often accumulates silently in software systems, impacting maintainability, scalability, and development speed.  
This project introduces a multi-agent architecture that applies modern LLMs to detect, explain, and propose fixes for Technical Debt (TD) in codebases.

The system is suitable for:
- Code review automation
- Continuous integration & quality gates
- Educational tooling
- Software maintenance research

---

## 🎯 Key Features

✔ Upload files or entire repos  
✔ Language-aware code slicing (Java supported first)  
✔ Class-level & method-level TD detection  
✔ Line-level smell localization  
✔ Human-readable explanations  
✔ Optional refactoring suggestions  
✔ Structured JSON output for integrations  

---

## 🏗 Multi-Agent System Architecture

Our system operates through cooperating specialized agents:

---

### **1. Source Code Loader**
- Loads source files or folders
- Detects programming language (Java/Python/C#/C++/JS/…)
- _Future:_ Tracks modified files across commits
- Forwards raw code to `ProgramSlicer`

---

### **2. Program Slicer**
- Splits code into smaller semantic slices:
  - Classes
  - Methods
- Uses language-aware slicing (**currently Java only**)
- Produces minimal slices to reduce LLM noise

---

### **3. Coordinator Agent**
Acts as the “brain” of the pipeline:

- Routes class slices → `Class Debt Detector`
- Routes method slices → `Method Debt Detector`
- Applies decision logic:
  - If no debt → skip
  - If debt → trigger explanation & fix suggestions

---

### **4. Class Debt Detector**  

Detects class-level smells:
- Blob Class
- Data Class

**Why a separate model?**
- Class-level abstraction benefits from larger context
- Reduces interference from method noise

---

### **5. Method Debt Detector**  

Detects method-level smells:
- Long Method
- Feature Envy
- Excessive Nesting
- Complex Branching

**Why slicing matters:**
- Only analyzes one function at a time
- Reduces model overwhelm
- Improves detection precision

---

### **6. Result Aggregator**
- Merges class-level + method-level detections
- Outputs unified structured results

---

### **7. Localization Agent**
Adds contextual metadata:
- File path
- Slice index
- Start/end line numbers

---

### **8. Explanation Agent**
Generates human-friendly details:
- Why it is considered debt
- Symptoms detected
- Potential consequences

Useful for:
- Code review
- Developer onboarding
- Educational tooling

---

### **9. Fix Suggestion Agent**
Produces improvement proposals:
- Light refactor suggestions
- Optional code rewrites
- Optional before/after diff-like output

---

## 🖥 Frontend Capabilities

Frontend supports:
- File or folder uploads
- Drag-and-drop UI
- Multi-language inputs (Java/C#/C++/Python/JS)

Configuration options:
- Class-level detection **on/off**
- Method-level detection **on/off**
- Slicing **on/off**
- Explanation **on/off**
- Fix suggestion **on/off**
- Minimum confidence threshold

---

## 📊 Output Example (JSON Structure)

```json
[
  {
    "file": "src/Foo.java",
    "type": "BlobClass",
    "lines": [12, 210],
    "explanation": "...",
    "suggestion": "Extract related functionality into cohesive classes."
  }
]
```
---
package com.example.samples;

import java.util.List;
import java.util.ArrayList;

/**
 * REFUSED BEQUEST - Examples of subclasses that ignore their parent's interface.
 * 
 * The inheritance relationship is semantically inappropriate: the child class
 * conceptually does not belong in the hierarchy and inherits methods that make
 * no sense in its domain context.
 */

// ============================================================================
// Example 1: Stack should not extend Vector
// A classic real-world example from Java's standard library.
// Stack is conceptually a LIFO data structure but inherits Vector's
// random-access, indexed-insertion, and enumeration methods.
// ============================================================================

abstract class DynamicArray {
    protected Object[] elements;
    protected int size;

    public void add(Object element) {
        ensureCapacity();
        elements[size++] = element;
    }

    public Object get(int index) {
        if (index < 0 || index >= size) throw new IndexOutOfBoundsException();
        return elements[index];
    }

    public void set(int index, Object element) {
        if (index < 0 || index >= size) throw new IndexOutOfBoundsException();
        elements[index] = element;
    }

    public void insertAt(int index, Object element) {
        ensureCapacity();
        System.arraycopy(elements, index, elements, index + 1, size - index);
        elements[index] = element;
        size++;
    }

    public Object removeAt(int index) {
        Object old = elements[index];
        System.arraycopy(elements, index + 1, elements, index, size - index - 1);
        size--;
        return old;
    }

    public int size() { return size; }

    public int indexOf(Object o) {
        for (int i = 0; i < size; i++) {
            if (elements[i].equals(o)) return i;
        }
        return -1;
    }

    public boolean contains(Object o) { return indexOf(o) >= 0; }

    public void clear() { size = 0; }

    protected void ensureCapacity() {
        if (elements == null) elements = new Object[10];
        if (size >= elements.length) {
            Object[] bigger = new Object[elements.length * 2];
            System.arraycopy(elements, 0, bigger, 0, size);
            elements = bigger;
        }
    }
}

/**
 * REFUSED BEQUEST: SimpleStack extends DynamicArray but only meaningfully uses
 * add() as push() and removeAt() as pop(). It inherits get(), set(), insertAt(),
 * indexOf(), contains() — none of which are appropriate for a stack's interface.
 * The child ignores 7 out of 10 parent methods.
 */
public class SimpleStack extends DynamicArray {

    public void push(Object item) {
        add(item);  // Only parent method that makes sense
    }

    public Object pop() {
        if (size == 0) throw new RuntimeException("Stack is empty");
        return removeAt(size - 1);  // Reuses parent but conceptually wrong inheritance
    }

    public Object peek() {
        if (size == 0) throw new RuntimeException("Stack is empty");
        return elements[size - 1];
    }

    public boolean isEmpty() {
        return size == 0;
    }

    // None of the inherited methods (get, set, insertAt, indexOf, contains, clear)
    // are overridden or make semantic sense for a Stack.
    // A stack should NOT allow random access or indexed insertion.
}


// ============================================================================
// Example 2: DataExporter extends AbstractReportGenerator but uses almost none
// of its reporting interface. The inheritance was chosen for code reuse only.
// ============================================================================

abstract class AbstractReportGenerator {
    protected String title;
    protected String author;
    protected List<String> sections;

    public AbstractReportGenerator(String title, String author) {
        this.title = title;
        this.author = author;
        this.sections = new ArrayList<>();
    }

    public abstract String generateHeader();
    public abstract String generateFooter();
    public abstract String formatSection(String content);
    public abstract void addTableOfContents();
    public abstract void addPageNumbers();
    public abstract String renderToHTML();
    public abstract String renderToPDF();

    public void addSection(String section) {
        sections.add(section);
    }

    public String getTitle() { return title; }
    public String getAuthor() { return author; }
}

/**
 * REFUSED BEQUEST: DataExporter inherits a rich report-generation interface but
 * only needs addSection() and the title field. It stubs out generateHeader,
 * generateFooter, formatSection, addTableOfContents, addPageNumbers, renderToHTML,
 * and renderToPDF with empty/trivial implementations.
 */
class DataExporter extends AbstractReportGenerator {
    private String delimiter;

    public DataExporter(String title, String delimiter) {
        super(title, "system");  // author is meaningless for CSV export
        this.delimiter = delimiter;
    }

    // All abstract methods stubbed out — semantically meaningless for CSV export
    @Override
    public String generateHeader() { return ""; }

    @Override
    public String generateFooter() { return ""; }

    @Override
    public String formatSection(String content) { return content; }

    @Override
    public void addTableOfContents() { /* no-op: CSVs don't have TOCs */ }

    @Override
    public void addPageNumbers() { /* no-op: CSVs don't have pages */ }

    @Override
    public String renderToHTML() { return ""; }  // Not applicable

    @Override
    public String renderToPDF() { return ""; }  // Not applicable

    // The actual functionality — completely unrelated to report generation
    public String exportToCSV(List<String[]> data) {
        StringBuilder sb = new StringBuilder();
        for (String[] row : data) {
            sb.append(String.join(delimiter, row)).append("\n");
        }
        return sb.toString();
    }

    public void exportToFile(List<String[]> data, String filePath) {
        String csv = exportToCSV(data);
        // Write to file...
    }
}

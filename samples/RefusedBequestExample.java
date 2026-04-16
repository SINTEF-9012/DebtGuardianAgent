package com.example.samples;

import java.util.List;
import java.util.ArrayList;

// --- DynamicArray and SimpleStack ---

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

/** SimpleStack — LIFO wrapper backed by DynamicArray */
public class SimpleStack extends DynamicArray {

    public void push(Object item) {
        add(item);
    }

    public Object pop() {
        if (size == 0) throw new RuntimeException("Stack is empty");
        return removeAt(size - 1);
    }

    public Object peek() {
        if (size == 0) throw new RuntimeException("Stack is empty");
        return elements[size - 1];
    }

    public boolean isEmpty() {
        return size == 0;
    }
}


// --- AbstractReportGenerator and DataExporter ---

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

/** DataExporter — CSV export backed by AbstractReportGenerator */
class DataExporter extends AbstractReportGenerator {
    private String delimiter;

    public DataExporter(String title, String delimiter) {
        super(title, "system");
        this.delimiter = delimiter;
    }

    @Override
    public String generateHeader() { return ""; }

    @Override
    public String generateFooter() { return ""; }

    @Override
    public String formatSection(String content) { return content; }

    @Override
    public void addTableOfContents() { }

    @Override
    public void addPageNumbers() { }

    @Override
    public String renderToHTML() { return ""; }

    @Override
    public String renderToPDF() { return ""; }

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

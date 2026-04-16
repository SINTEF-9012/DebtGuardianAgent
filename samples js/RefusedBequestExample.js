const fs = require("fs");

// --- DynamicArray and SimpleStack ---

class DynamicArray {
    constructor() {
        this.elements = [];
    }

    add(element) {
        this.elements.push(element);
    }

    get(index) {
        if (index < 0 || index >= this.elements.length) throw new RangeError("Index out of bounds");
        return this.elements[index];
    }

    set(index, element) {
        if (index < 0 || index >= this.elements.length) throw new RangeError("Index out of bounds");
        this.elements[index] = element;
    }

    insertAt(index, element) {
        this.elements.splice(index, 0, element);
    }

    removeAt(index) {
        return this.elements.splice(index, 1)[0];
    }

    size() {
        return this.elements.length;
    }

    indexOf(o) {
        return this.elements.indexOf(o);
    }

    contains(o) {
        return this.indexOf(o) >= 0;
    }

    clear() {
        this.elements.length = 0;
    }
}

/** SimpleStack — LIFO wrapper backed by DynamicArray */
class SimpleStack extends DynamicArray {
    push(item) {
        this.add(item);
    }

    pop() {
        if (this.elements.length === 0) throw new Error("Stack is empty");
        return this.removeAt(this.elements.length - 1);
    }

    peek() {
        if (this.elements.length === 0) throw new Error("Stack is empty");
        return this.elements[this.elements.length - 1];
    }

    isEmpty() {
        return this.elements.length === 0;
    }
}


// --- AbstractReportGenerator and DataExporter ---

class AbstractReportGenerator {
    constructor(title, author) {
        this.title = title;
        this.author = author;
        this.sections = [];
    }

    generateHeader() { throw new Error("Not implemented"); }
    generateFooter() { throw new Error("Not implemented"); }
    formatSection(content) { throw new Error("Not implemented"); }
    addTableOfContents() { throw new Error("Not implemented"); }
    addPageNumbers() { throw new Error("Not implemented"); }
    renderToHTML() { throw new Error("Not implemented"); }
    renderToPDF() { throw new Error("Not implemented"); }

    addSection(section) {
        this.sections.push(section);
    }
}

/** DataExporter — CSV export backed by AbstractReportGenerator */
class DataExporter extends AbstractReportGenerator {
    constructor(title, delimiter) {
        super(title, "system");
        this.delimiter = delimiter;
    }

    generateHeader() { return ""; }
    generateFooter() { return ""; }
    formatSection(content) { return content; }
    addTableOfContents() { /* no-op */ }
    addPageNumbers() { /* no-op */ }
    renderToHTML() { return ""; }
    renderToPDF() { return ""; }

    exportToCSV(data) {
        return data.map(row => row.join(this.delimiter)).join("\n");
    }

    exportToFile(data, filePath) {
        const csv = this.exportToCSV(data);
        fs.writeFileSync(filePath, csv);
    }
}

module.exports = { DynamicArray, SimpleStack, AbstractReportGenerator, DataExporter };

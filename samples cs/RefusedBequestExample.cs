using System;
using System.Collections.Generic;

/// <summary>
/// REFUSED BEQUEST - Examples of subclasses that ignore their parent's interface.
///
/// The inheritance relationship is semantically inappropriate: the child class
/// conceptually does not belong in the hierarchy and inherits methods that make
/// no sense in its domain context.
/// </summary>

// ============================================================================
// Example 1: Stack should not extend DynamicArray
// Stack is conceptually a LIFO data structure but inherits random-access,
// indexed-insertion, and enumeration methods.
// ============================================================================

public abstract class DynamicArray
{
    protected object[] elements;
    protected int count;

    public void Add(object element)
    {
        EnsureCapacity();
        elements[count++] = element;
    }

    public object Get(int index)
    {
        if (index < 0 || index >= count) throw new IndexOutOfRangeException();
        return elements[index];
    }

    public void Set(int index, object element)
    {
        if (index < 0 || index >= count) throw new IndexOutOfRangeException();
        elements[index] = element;
    }

    public void InsertAt(int index, object element)
    {
        EnsureCapacity();
        Array.Copy(elements, index, elements, index + 1, count - index);
        elements[index] = element;
        count++;
    }

    public object RemoveAt(int index)
    {
        object old = elements[index];
        Array.Copy(elements, index + 1, elements, index, count - index - 1);
        count--;
        return old;
    }

    public int Count => count;

    public int IndexOf(object o)
    {
        for (int i = 0; i < count; i++)
        {
            if (elements[i].Equals(o)) return i;
        }
        return -1;
    }

    public bool Contains(object o) => IndexOf(o) >= 0;

    public void Clear() { count = 0; }

    protected void EnsureCapacity()
    {
        if (elements == null) elements = new object[10];
        if (count >= elements.Length)
        {
            var bigger = new object[elements.Length * 2];
            Array.Copy(elements, bigger, count);
            elements = bigger;
        }
    }
}

/// <summary>
/// REFUSED BEQUEST: SimpleStack extends DynamicArray but only meaningfully uses
/// Add() as Push() and RemoveAt() as Pop(). It inherits Get(), Set(), InsertAt(),
/// IndexOf(), Contains() — none of which are appropriate for a stack's interface.
/// The child ignores 7 out of 10 parent methods.
/// </summary>
public class SimpleStack : DynamicArray
{
    public void Push(object item)
    {
        Add(item); // Only parent method that makes sense
    }

    public object Pop()
    {
        if (count == 0) throw new InvalidOperationException("Stack is empty");
        return RemoveAt(count - 1);
    }

    public object Peek()
    {
        if (count == 0) throw new InvalidOperationException("Stack is empty");
        return elements[count - 1];
    }

    public bool IsEmpty => count == 0;

    // None of the inherited methods (Get, Set, InsertAt, IndexOf, Contains, Clear)
    // are overridden or make semantic sense for a Stack.
    // A stack should NOT allow random access or indexed insertion.
}


// ============================================================================
// Example 2: DataExporter extends AbstractReportGenerator but uses almost none
// of its reporting interface. The inheritance was chosen for code reuse only.
// ============================================================================

public abstract class AbstractReportGenerator
{
    protected string Title;
    protected string Author;
    protected List<string> Sections;

    protected AbstractReportGenerator(string title, string author)
    {
        Title = title;
        Author = author;
        Sections = new List<string>();
    }

    public abstract string GenerateHeader();
    public abstract string GenerateFooter();
    public abstract string FormatSection(string content);
    public abstract void AddTableOfContents();
    public abstract void AddPageNumbers();
    public abstract string RenderToHtml();
    public abstract string RenderToPdf();

    public void AddSection(string section) => Sections.Add(section);
    public string GetTitle() => Title;
    public string GetAuthor() => Author;
}

/// <summary>
/// REFUSED BEQUEST: DataExporter inherits a rich report-generation interface but
/// only needs AddSection() and the Title field. It stubs out GenerateHeader,
/// GenerateFooter, FormatSection, AddTableOfContents, AddPageNumbers, RenderToHtml,
/// and RenderToPdf with empty/trivial implementations.
/// </summary>
public class DataExporter : AbstractReportGenerator
{
    private readonly string _delimiter;

    public DataExporter(string title, string delimiter)
        : base(title, "system") // author is meaningless for CSV export
    {
        _delimiter = delimiter;
    }

    // All abstract methods stubbed out — semantically meaningless for CSV export
    public override string GenerateHeader() => "";
    public override string GenerateFooter() => "";
    public override string FormatSection(string content) => content;
    public override void AddTableOfContents() { /* no-op: CSVs don't have TOCs */ }
    public override void AddPageNumbers() { /* no-op: CSVs don't have pages */ }
    public override string RenderToHtml() => ""; // Not applicable
    public override string RenderToPdf() => ""; // Not applicable

    // The actual functionality — completely unrelated to report generation
    public string ExportToCsv(List<string[]> data)
    {
        var sb = new System.Text.StringBuilder();
        foreach (var row in data)
        {
            sb.AppendLine(string.Join(_delimiter, row));
        }
        return sb.ToString();
    }

    public void ExportToFile(List<string[]> data, string filePath)
    {
        string csv = ExportToCsv(data);
        System.IO.File.WriteAllText(filePath, csv);
    }
}

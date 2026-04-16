using System;
using System.Collections.Generic;

// --- DynamicArray and SimpleStack ---

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
/// SimpleStack — LIFO wrapper backed by DynamicArray
/// </summary>
public class SimpleStack : DynamicArray
{
    public void Push(object item)
    {
        Add(item);
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
}


// --- AbstractReportGenerator and DataExporter ---

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
/// DataExporter — CSV export backed by AbstractReportGenerator
/// </summary>
public class DataExporter : AbstractReportGenerator
{
    private readonly string _delimiter;

    public DataExporter(string title, string delimiter)
        : base(title, "system")
    {
        _delimiter = delimiter;
    }

    public override string GenerateHeader() => "";
    public override string GenerateFooter() => "";
    public override string FormatSection(string content) => content;
    public override void AddTableOfContents() { }
    public override void AddPageNumbers() { }
    public override string RenderToHtml() => "";
    public override string RenderToPdf() => "";

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

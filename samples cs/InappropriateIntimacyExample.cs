using System;
using System.Collections.Generic;

// --- Lexer, Parser, and supporting Token class ---

public class Token
{
    public string Type;
    public string Value;
    public int Line;
    public int Column;

    public Token(string type, string value, int line, int column)
    {
        Type = type;
        Value = value;
        Line = line;
        Column = column;
    }
}

public class Lexer
{
    // Internal state that Parser should NOT directly access
    public string Source;
    public int CurrentPos;
    public int CurrentLine;
    public int CurrentColumn;
    public List<Token> TokenBuffer;
    public List<string> ErrorList;
    public bool HasErrors;

    // Reference to Parser — creates bidirectional dependency
    public Parser Parser;

    public Lexer(string source)
    {
        Source = source;
        CurrentPos = 0;
        CurrentLine = 1;
        CurrentColumn = 1;
        TokenBuffer = new List<Token>();
        ErrorList = new List<string>();
        HasErrors = false;
    }

    public void Tokenize()
    {
        while (CurrentPos < Source.Length)
        {
            char c = Source[CurrentPos];

            if (char.IsWhiteSpace(c))
            {
                Advance();
                continue;
            }

            if (Parser.ParseStack.Count > 0)
            {
                string context = Parser.ParseStack[Parser.ParseStack.Count - 1];
                if (context == "STRING_LITERAL")
                {
                    TokenizeStringContent();
                    continue;
                }
            }

            if (c == '#' && CurrentPos + 1 < Source.Length
                    && Source[CurrentPos + 1] == '!')
            {
                Parser.ErrorCount++;
                Parser.LastError = "Unexpected preprocessor directive at line " + CurrentLine;
                ErrorList.Add(Parser.LastError);
            }

            if (char.IsLetter(c))
            {
                string word = ReadWord();
                if (Parser.SymbolTable.ContainsKey(word))
                {
                    string symbolType = Parser.SymbolTable[word];
                    TokenBuffer.Add(new Token(symbolType, word, CurrentLine, CurrentColumn));
                }
                else
                {
                    TokenBuffer.Add(new Token("IDENTIFIER", word, CurrentLine, CurrentColumn));
                }
                continue;
            }

            TokenBuffer.Add(new Token("SYMBOL", c.ToString(), CurrentLine, CurrentColumn));
            Advance();
        }
    }

    public void RewindTo(int position)
    {
        CurrentPos = position;
    }

    private void Advance()
    {
        CurrentPos++;
        CurrentColumn++;
    }

    private string ReadWord()
    {
        int start = CurrentPos;
        while (CurrentPos < Source.Length && char.IsLetterOrDigit(Source[CurrentPos]))
        {
            Advance();
        }
        return Source.Substring(start, CurrentPos - start);
    }

    private void TokenizeStringContent()
    {
        Parser.InStringLiteral = true;
        int start = CurrentPos;
        while (CurrentPos < Source.Length && Source[CurrentPos] != '"')
        {
            Advance();
        }
        TokenBuffer.Add(new Token("STRING_CONTENT",
            Source.Substring(start, CurrentPos - start), CurrentLine, CurrentColumn));
        Parser.InStringLiteral = false;
    }
}


public class Parser
{
    public List<string> ParseStack;
    public Dictionary<string, string> SymbolTable;
    public int ErrorCount;
    public string LastError;
    public bool InStringLiteral;
    public List<object> AstNodes;

    public Lexer Lexer;

    public Parser(Lexer lexer)
    {
        Lexer = lexer;
        ParseStack = new List<string>();
        SymbolTable = new Dictionary<string, string>();
        AstNodes = new List<object>();
        ErrorCount = 0;
        InStringLiteral = false;
    }

    public void Parse()
    {
        for (int i = 0; i < Lexer.TokenBuffer.Count; i++)
        {
            Token token = Lexer.TokenBuffer[i];

            int savedPos = Lexer.CurrentPos;

            if (token.Type == "IDENTIFIER")
            {
                ParseIdentifier(token);
            }
            else if (token.Type == "SYMBOL")
            {
                ParseSymbol(token, i);
            }

            if (Lexer.HasErrors)
            {
                ErrorCount += Lexer.ErrorList.Count;
                Lexer.ErrorList.Clear();
                Lexer.HasErrors = false;
            }
        }
    }

    private void ParseIdentifier(Token token)
    {
        SymbolTable[token.Value] = "VARIABLE";
        ParseStack.Add(token.Value);

        if (token.Value == "var")
        {
            Lexer.TokenBuffer.Add(
                new Token("TYPE_INFERRED", "auto", token.Line, token.Column));
        }
    }

    private void ParseSymbol(Token token, int index)
    {
        if (token.Value == "\"")
        {
            ParseStack.Add("STRING_LITERAL");

            Lexer.CurrentPos = FindSourcePosition(token);
            Lexer.Tokenize(); // Forces re-tokenization from modified position
        }

        if (token.Value == "{")
        {
            ParseStack.Add("BLOCK");
        }
        else if (token.Value == "}")
        {
            if (ParseStack.Count > 0)
            {
                ParseStack.RemoveAt(ParseStack.Count - 1);
            }
        }
    }

    private int FindSourcePosition(Token token)
    {
        string source = Lexer.Source;
        int line = 1, col = 1;
        for (int i = 0; i < source.Length; i++)
        {
            if (line == token.Line && col == token.Column) return i;
            if (source[i] == '\n') { line++; col = 1; }
            else col++;
        }
        return 0;
    }
}


// --- SessionManager and SecurityContext ---

public class SecurityContext
{
    // Internal state
    public string CurrentUserId;
    public List<string> Permissions;
    public Dictionary<string, long> TokenExpirations;
    public bool Locked;

    // Bidirectional reference
    public SessionManager SessionManager;

    public SecurityContext()
    {
        Permissions = new List<string>();
        TokenExpirations = new Dictionary<string, long>();
        Locked = false;
    }

    public void Authenticate(string userId, string password)
    {
        CurrentUserId = userId;
        Permissions = LoadPermissions(userId);

        if (SessionManager.ActiveSessions.ContainsKey(userId))
        {
            SessionManager.ActiveSessions[userId].LastActivity =
                DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        }
        else
        {
            var session = new Session(userId);
            SessionManager.ActiveSessions[userId] = session;
            SessionManager.SessionCount++;
        }
    }

    public bool HasPermission(string action)
    {
        if (SessionManager.TimeoutOverrides.ContainsKey(CurrentUserId))
        {
            long timeout = SessionManager.TimeoutOverrides[CurrentUserId];
            if (DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() > timeout)
            {
                return false;
            }
        }
        return Permissions.Contains(action);
    }

    private List<string> LoadPermissions(string userId) => new List<string>();
}


public class SessionManager
{
    // Internal state
    public Dictionary<string, Session> ActiveSessions;
    public Dictionary<string, long> TimeoutOverrides;
    public int SessionCount;
    public int MaxSessions;

    // Bidirectional reference
    public SecurityContext SecurityContext;

    public SessionManager(int maxSessions)
    {
        ActiveSessions = new Dictionary<string, Session>();
        TimeoutOverrides = new Dictionary<string, long>();
        SessionCount = 0;
        MaxSessions = maxSessions;
    }

    public void CreateSession(string userId)
    {
        if (SecurityContext.Permissions.Contains("ADMIN"))
        {
            ActiveSessions[userId] = new Session(userId);
        }
        else if (SessionCount < MaxSessions)
        {
            ActiveSessions[userId] = new Session(userId);
            SessionCount++;
        }

        if (SessionCount >= MaxSessions)
        {
            SecurityContext.Locked = true;
        }
    }

    public void DestroySession(string userId)
    {
        ActiveSessions.Remove(userId);
        SessionCount--;

        SecurityContext.Locked = false;
        SecurityContext.CurrentUserId = null;
        SecurityContext.Permissions.Clear();
    }

    public void RefreshSession(string userId)
    {
        if (ActiveSessions.TryGetValue(userId, out var session))
        {
            session.LastActivity = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

            if (SecurityContext.TokenExpirations.TryGetValue(userId, out long expiry)
                && DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() > expiry)
            {
                DestroySession(userId);
            }
        }
    }
}

public class Session
{
    public string UserId;
    public long CreatedAt;
    public long LastActivity;

    public Session(string userId)
    {
        UserId = userId;
        CreatedAt = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        LastActivity = CreatedAt;
    }
}

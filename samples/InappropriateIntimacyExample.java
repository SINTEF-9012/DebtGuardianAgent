package com.example.samples;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

/**
 * INAPPROPRIATE INTIMACY - Two classes that excessively access each other's
 * internal details, creating tight bidirectional coupling.
 * 
 * This smell is subtle because SOME bidirectional coupling is normal (e.g.,
 * Order/OrderLine). The key distinction is whether the coupling involves
 * reaching into internal state vs. using a well-defined public interface.
 * 
 * Static tools can count bidirectional references, but they cannot judge whether
 * the coupling is "inappropriate" vs. architecturally justified. An LLM can
 * reason about the domain roles of the classes and whether they should be
 * merged, decoupled, or are correctly intertwined.
 */

// ============================================================================
// Example 1: Parser and Lexer with excessive mutual access to internals
// These classes reach into each other's private fields and modify internal
// state directly, rather than communicating through a clean interface.
// ============================================================================

class Token {
    String type;
    String value;
    int line;
    int column;

    Token(String type, String value, int line, int column) {
        this.type = type;
        this.value = value;
        this.line = line;
        this.column = column;
    }
}

class Lexer {
    // Internal state that Parser should NOT directly access
    String source;
    int currentPos;
    int currentLine;
    int currentColumn;
    List<Token> tokenBuffer;
    List<String> errorList;
    boolean hasErrors;
    
    // Reference to Parser — creates bidirectional dependency
    Parser parser;

    public Lexer(String source) {
        this.source = source;
        this.currentPos = 0;
        this.currentLine = 1;
        this.currentColumn = 1;
        this.tokenBuffer = new ArrayList<>();
        this.errorList = new ArrayList<>();
        this.hasErrors = false;
    }

    public void setParser(Parser parser) {
        this.parser = parser;
    }

    public void tokenize() {
        while (currentPos < source.length()) {
            char c = source.charAt(currentPos);

            if (Character.isWhitespace(c)) {
                advance();
                continue;
            }

            // INAPPROPRIATE: Directly accesses Parser's internal parseStack
            // to decide how to tokenize context-sensitively
            if (parser.parseStack.size() > 0) {
                String context = parser.parseStack.get(parser.parseStack.size() - 1);
                if (context.equals("STRING_LITERAL")) {
                    tokenizeStringContent();
                    continue;
                }
            }

            // INAPPROPRIATE: Directly modifies Parser's internal error count
            if (c == '#' && currentPos + 1 < source.length() 
                    && source.charAt(currentPos + 1) == '!') {
                parser.errorCount++;
                parser.lastError = "Unexpected preprocessor directive at line " + currentLine;
                errorList.add(parser.lastError);
            }

            // INAPPROPRIATE: Reads Parser's internal symbol table to resolve ambiguity
            if (Character.isLetter(c)) {
                String word = readWord();
                if (parser.symbolTable.containsKey(word)) {
                    // Check parser's symbol table to determine token type
                    String symbolType = parser.symbolTable.get(word);
                    tokenBuffer.add(new Token(symbolType, word, currentLine, currentColumn));
                } else {
                    tokenBuffer.add(new Token("IDENTIFIER", word, currentLine, currentColumn));
                }
                continue;
            }

            tokenBuffer.add(new Token("SYMBOL", String.valueOf(c), currentLine, currentColumn));
            advance();
        }
    }

    // INAPPROPRIATE: Parser calls this to directly manipulate Lexer's position
    public void rewindTo(int position) {
        this.currentPos = position;
    }

    private void advance() {
        currentPos++;
        currentColumn++;
    }

    private String readWord() {
        int start = currentPos;
        while (currentPos < source.length() && Character.isLetterOrDigit(source.charAt(currentPos))) {
            advance();
        }
        return source.substring(start, currentPos);
    }

    private void tokenizeStringContent() {
        // INAPPROPRIATE: Modifies Parser's state while tokenizing
        parser.inStringLiteral = true;
        int start = currentPos;
        while (currentPos < source.length() && source.charAt(currentPos) != '"') {
            advance();
        }
        tokenBuffer.add(new Token("STRING_CONTENT", source.substring(start, currentPos),
                                  currentLine, currentColumn));
        parser.inStringLiteral = false;
    }
}


class Parser {
    // Internal state that Lexer should NOT directly access
    List<String> parseStack;
    Map<String, String> symbolTable;
    int errorCount;
    String lastError;
    boolean inStringLiteral;
    List<Object> astNodes;

    // Reference to Lexer — creates bidirectional dependency
    Lexer lexer;

    public Parser(Lexer lexer) {
        this.lexer = lexer;
        this.parseStack = new ArrayList<>();
        this.symbolTable = new HashMap<>();
        this.astNodes = new ArrayList<>();
        this.errorCount = 0;
        this.inStringLiteral = false;
    }

    public void parse() {
        // INAPPROPRIATE: Directly accesses Lexer's internal tokenBuffer
        for (int i = 0; i < lexer.tokenBuffer.size(); i++) {
            Token token = lexer.tokenBuffer.get(i);

            // INAPPROPRIATE: Directly reads/writes Lexer's internal position
            int savedPos = lexer.currentPos;
            
            if (token.type.equals("IDENTIFIER")) {
                parseIdentifier(token);
            } else if (token.type.equals("SYMBOL")) {
                parseSymbol(token, i);
            }

            // INAPPROPRIATE: Directly checks Lexer's error state
            if (lexer.hasErrors) {
                errorCount += lexer.errorList.size();
                lexer.errorList.clear();  // Directly modifies Lexer's internal list
                lexer.hasErrors = false;  // Directly modifies Lexer's internal flag
            }
        }
    }

    private void parseIdentifier(Token token) {
        symbolTable.put(token.value, "VARIABLE");
        parseStack.add(token.value);

        // INAPPROPRIATE: Directly manipulates Lexer's tokenBuffer to insert synthetic tokens
        if (token.value.equals("var")) {
            lexer.tokenBuffer.add(new Token("TYPE_INFERRED", "auto", token.line, token.column));
        }
    }

    private void parseSymbol(Token token, int index) {
        if (token.value.equals("\"")) {
            parseStack.add("STRING_LITERAL");
            
            // INAPPROPRIATE: Tells Lexer to re-tokenize from this position
            // by directly manipulating Lexer's internal position
            lexer.currentPos = findSourcePosition(token);
            lexer.tokenize();  // Forces re-tokenization from modified position
        }

        if (token.value.equals("{")) {
            parseStack.add("BLOCK");
        } else if (token.value.equals("}")) {
            if (!parseStack.isEmpty()) {
                parseStack.remove(parseStack.size() - 1);
            }
        }
    }

    private int findSourcePosition(Token token) {
        // INAPPROPRIATE: Accesses Lexer's internal source string
        String source = lexer.source;
        int line = 1;
        int col = 1;
        for (int i = 0; i < source.length(); i++) {
            if (line == token.line && col == token.column) return i;
            if (source.charAt(i) == '\n') { line++; col = 1; }
            else col++;
        }
        return 0;
    }
}


// ============================================================================
// Example 2: SessionManager and SecurityContext with bidirectional intimacy
// ============================================================================

class SecurityContext {
    // Internal state
    String currentUserId;
    List<String> permissions;
    Map<String, Long> tokenExpirations;
    boolean locked;

    // Bidirectional reference
    SessionManager sessionManager;

    public SecurityContext() {
        this.permissions = new ArrayList<>();
        this.tokenExpirations = new HashMap<>();
        this.locked = false;
    }

    public void authenticate(String userId, String password) {
        this.currentUserId = userId;
        this.permissions = loadPermissions(userId);

        // INAPPROPRIATE: Directly accesses SessionManager's internal session map
        if (sessionManager.activeSessions.containsKey(userId)) {
            // Directly modifies SessionManager's internal state
            sessionManager.activeSessions.get(userId).lastActivity = System.currentTimeMillis();
        } else {
            // Directly creates entries in SessionManager's internal map
            Session session = new Session(userId);
            sessionManager.activeSessions.put(userId, session);
            sessionManager.sessionCount++;
        }
    }

    public boolean hasPermission(String action) {
        // INAPPROPRIATE: Checks SessionManager's internal timeout map
        if (sessionManager.timeoutOverrides.containsKey(currentUserId)) {
            long timeout = sessionManager.timeoutOverrides.get(currentUserId);
            if (System.currentTimeMillis() > timeout) {
                return false;
            }
        }
        return permissions.contains(action);
    }

    private List<String> loadPermissions(String userId) {
        return new ArrayList<>();
    }
}


class SessionManager {
    // Internal state
    Map<String, Session> activeSessions;
    Map<String, Long> timeoutOverrides;
    int sessionCount;
    int maxSessions;

    // Bidirectional reference
    SecurityContext securityContext;

    public SessionManager(int maxSessions) {
        this.activeSessions = new HashMap<>();
        this.timeoutOverrides = new HashMap<>();
        this.sessionCount = 0;
        this.maxSessions = maxSessions;
    }

    public void createSession(String userId) {
        // INAPPROPRIATE: Directly reads SecurityContext's internal permissions
        if (securityContext.permissions.contains("ADMIN")) {
            // Admins bypass session limits
            activeSessions.put(userId, new Session(userId));
        } else if (sessionCount < maxSessions) {
            activeSessions.put(userId, new Session(userId));
            sessionCount++;
        }

        // INAPPROPRIATE: Directly modifies SecurityContext's lock state
        if (sessionCount >= maxSessions) {
            securityContext.locked = true;
        }
    }

    public void destroySession(String userId) {
        activeSessions.remove(userId);
        sessionCount--;

        // INAPPROPRIATE: Directly modifies SecurityContext's internal state
        securityContext.locked = false;
        securityContext.currentUserId = null;
        securityContext.permissions.clear();
    }

    public void refreshSession(String userId) {
        Session session = activeSessions.get(userId);
        if (session != null) {
            session.lastActivity = System.currentTimeMillis();
            
            // INAPPROPRIATE: Directly reads SecurityContext's token expirations
            Long expiry = securityContext.tokenExpirations.get(userId);
            if (expiry != null && System.currentTimeMillis() > expiry) {
                destroySession(userId);
            }
        }
    }
}

class Session {
    String userId;
    long createdAt;
    long lastActivity;

    Session(String userId) {
        this.userId = userId;
        this.createdAt = System.currentTimeMillis();
        this.lastActivity = this.createdAt;
    }
}

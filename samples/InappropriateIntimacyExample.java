package com.example.samples;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

// --- Parser, Lexer, and supporting Token class ---

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
    // Internal state
    String source;
    int currentPos;
    int currentLine;
    int currentColumn;
    List<Token> tokenBuffer;
    List<String> errorList;
    boolean hasErrors;
    
    // Reference to Parser
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

            if (parser.parseStack.size() > 0) {
                String context = parser.parseStack.get(parser.parseStack.size() - 1);
                if (context.equals("STRING_LITERAL")) {
                    tokenizeStringContent();
                    continue;
                }
            }

            if (c == '#' && currentPos + 1 < source.length() 
                    && source.charAt(currentPos + 1) == '!') {
                parser.errorCount++;
                parser.lastError = "Unexpected preprocessor directive at line " + currentLine;
                errorList.add(parser.lastError);
            }

            if (Character.isLetter(c)) {
                String word = readWord();
                if (parser.symbolTable.containsKey(word)) {
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
    // Internal state
    List<String> parseStack;
    Map<String, String> symbolTable;
    int errorCount;
    String lastError;
    boolean inStringLiteral;
    List<Object> astNodes;

    // Reference to Lexer
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
        for (int i = 0; i < lexer.tokenBuffer.size(); i++) {
            Token token = lexer.tokenBuffer.get(i);

            int savedPos = lexer.currentPos;
            
            if (token.type.equals("IDENTIFIER")) {
                parseIdentifier(token);
            } else if (token.type.equals("SYMBOL")) {
                parseSymbol(token, i);
            }

            if (lexer.hasErrors) {
                errorCount += lexer.errorList.size();
                lexer.errorList.clear();
                lexer.hasErrors = false;
            }
        }
    }

    private void parseIdentifier(Token token) {
        symbolTable.put(token.value, "VARIABLE");
        parseStack.add(token.value);

        if (token.value.equals("var")) {
            lexer.tokenBuffer.add(new Token("TYPE_INFERRED", "auto", token.line, token.column));
        }
    }

    private void parseSymbol(Token token, int index) {
        if (token.value.equals("\"")) {
            parseStack.add("STRING_LITERAL");
            
            // Tells Lexer to re-tokenize from this position
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


// --- SecurityContext and SessionManager ---

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

        if (sessionManager.activeSessions.containsKey(userId)) {
            sessionManager.activeSessions.get(userId).lastActivity = System.currentTimeMillis();
        } else {
            Session session = new Session(userId);
            sessionManager.activeSessions.put(userId, session);
            sessionManager.sessionCount++;
        }
    }

    public boolean hasPermission(String action) {
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
        if (securityContext.permissions.contains("ADMIN")) {
            // Admins bypass session limits
            activeSessions.put(userId, new Session(userId));
        } else if (sessionCount < maxSessions) {
            activeSessions.put(userId, new Session(userId));
            sessionCount++;
        }

        if (sessionCount >= maxSessions) {
            securityContext.locked = true;
        }
    }

    public void destroySession(String userId) {
        activeSessions.remove(userId);
        sessionCount--;

        securityContext.locked = false;
        securityContext.currentUserId = null;
        securityContext.permissions.clear();
    }

    public void refreshSession(String userId) {
        Session session = activeSessions.get(userId);
        if (session != null) {
            session.lastActivity = System.currentTimeMillis();
            
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

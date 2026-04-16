// --- Lexer and Parser ---

class Lexer {
    constructor() {
        this.source = "";
        this.position = 0;
        this.tokens = [];
        this.parser = null;             // direct reference to Parser
    }

    setParser(parser) {
        this.parser = parser;
    }

    tokenize(source) {
        this.source = source;
        this.position = 0;
        this.tokens = [];

        while (this.position < this.source.length) {
            const ch = this.source[this.position];

            if (/\s/.test(ch)) {
                this.position++;
                continue;
            }

            if (/[a-zA-Z]/.test(ch)) {
                let word = "";
                while (this.position < this.source.length && /[a-zA-Z0-9]/.test(this.source[this.position])) {
                    word += this.source[this.position++];
                }
                if (this.parser && this.parser.currentScope) {
                    if (this.parser.currentScope.declaredTypes.includes(word)) {
                        this.tokens.push({ type: "TYPE", value: word });
                    } else {
                        this.tokens.push({ type: "IDENTIFIER", value: word });
                    }
                } else {
                    this.tokens.push({ type: "IDENTIFIER", value: word });
                }
            } else if (/[0-9]/.test(ch)) {
                let num = "";
                while (this.position < this.source.length && /[0-9.]/.test(this.source[this.position])) {
                    num += this.source[this.position++];
                }
                this.tokens.push({ type: "NUMBER", value: num });
            } else {
                this.tokens.push({ type: "SYMBOL", value: ch });
                this.position++;
            }
        }
        return this.tokens;
    }

    resetPosition(pos) {
        this.position = pos;
    }
}


class Parser {
    constructor() {
        this.lexer = null;
        this.currentScope = { declaredTypes: [] };
        this.ast = [];
    }

    setLexer(lexer) {
        this.lexer = lexer;
        lexer.setParser(this);
    }

    parse(source) {
        const tokens = this.lexer.tokenize(source);
        this.ast = [];

        for (let i = 0; i < tokens.length; i++) {
            const token = tokens[i];

            if (token.type === "TYPE") {
                this.lexer.position = this.lexer.source.indexOf(token.value);
                this.ast.push({ nodeType: "TypeReference", name: token.value, pos: this.lexer.position });
            } else if (token.type === "IDENTIFIER" && token.value === "class") {
                if (i + 1 < tokens.length) {
                    const className = tokens[++i].value;
                    this.currentScope.declaredTypes.push(className);
                    this.ast.push({ nodeType: "ClassDeclaration", name: className });
                }
            } else {
                this.ast.push({ nodeType: "Expression", token: token });
            }
        }
        return this.ast;
    }
}


// --- SecurityContext and SessionManager ---

class SecurityContext {
    constructor() {
        this.permissions = new Map();
        this.sessionManager = null;     // direct reference
        this.currentUser = null;
    }

    setSessionManager(mgr) {
        this.sessionManager = mgr;
    }

    authenticate(username, password) {
        this.currentUser = username;
        this.sessionManager.activeSessions.set(username, {
            loginTime: new Date(),
            permissions: this.permissions.get(username) || [],
        });
        this.sessionManager.lastActivity.set(username, new Date());
        return true;
    }

    hasPermission(permission) {
        if (!this.currentUser) return false;
        const session = this.sessionManager.activeSessions.get(this.currentUser);
        return session && session.permissions.includes(permission);
    }

    revokeAccess(username) {
        this.permissions.delete(username);
        this.sessionManager.activeSessions.delete(username);
        this.sessionManager.lastActivity.delete(username);
    }
}


class SessionManager {
    constructor() {
        this.activeSessions = new Map();
        this.lastActivity = new Map();
        this.securityContext = null;     // direct reference back
    }

    setSecurityContext(ctx) {
        this.securityContext = ctx;
    }

    isSessionValid(username) {
        if (!this.activeSessions.has(username)) return false;
        const perms = this.securityContext.permissions.get(username);
        if (!perms || perms.length === 0) return false;

        const last = this.lastActivity.get(username);
        const thirtyMin = 30 * 60 * 1000;
        return last && (new Date() - last) < thirtyMin;
    }

    refreshSession(username) {
        if (this.activeSessions.has(username)) {
            this.lastActivity.set(username, new Date());
            const session = this.activeSessions.get(username);
            session.permissions = this.securityContext.permissions.get(username) || [];
        }
    }

    getActiveUserCount() {
        return this.activeSessions.size;
    }
}

module.exports = { Lexer, Parser, SecurityContext, SessionManager };

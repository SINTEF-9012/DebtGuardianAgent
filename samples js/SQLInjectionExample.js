// --- UserRepository — database access layer ---

class UserRepository {
    constructor(db) {
        this.db = db;
    }

    findByUsername(username) {
        const sql = "SELECT * FROM users WHERE username = '" + username + "'";
        return this.db.query(sql);
    }

    findByEmail(email) {
        return this.db.query(`SELECT * FROM users WHERE email = '${email}'`);
    }

    search(name, role) {
        const sql = "SELECT * FROM users WHERE name LIKE '%" + name + "%'"
            + " AND role = '" + role + "'";
        return this.db.query(sql);
    }

    findAllSorted(sortColumn) {
        return this.db.query("SELECT * FROM users ORDER BY " + sortColumn);
    }

    createUser(username, email, role) {
        const sql = "INSERT INTO users (username, email, role) VALUES ('"
            + username + "', '" + email + "', '" + role + "')";
        return this.db.query(sql);
    }

    updateEmail(userId, newEmail) {
        return this.db.query(
            "UPDATE users SET email = '" + newEmail + "' WHERE id = " + userId
        );
    }

    deleteUser(userId) {
        return this.db.query("DELETE FROM users WHERE id = " + userId);
    }
}


// --- SystemUtils — OS-level operations ---

const { exec, execSync } = require("child_process");

class SystemUtils {

    ping(host) {
        return new Promise((resolve, reject) => {
            exec("ping -c 4 " + host, (err, stdout) => {
                if (err) reject(err);
                else resolve(stdout);
            });
        });
    }

    lookupDns(domain) {
        return execSync(`nslookup ${domain}`).toString();
    }

    compressFile(filePath) {
        exec("tar -czf archive.tar.gz " + filePath);
    }

    getFileInfo(fileName) {
        return execSync("file " + fileName + " && wc -l " + fileName).toString();
    }

    fetchUrl(url) {
        return new Promise((resolve, reject) => {
            exec("curl -s " + url, (err, stdout) => {
                if (err) reject(err);
                else resolve(stdout);
            });
        });
    }
}

module.exports = { UserRepository, SystemUtils };

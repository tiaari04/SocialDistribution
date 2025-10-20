"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.set = exports.remove = exports.add = exports.current = exports.list = void 0;
const yaml_1 = require("yaml");
const fs = require("fs");
const os = require("node:os");
const path = require("node:path");
const netrc_parser_1 = require("netrc-parser");
function configDir() {
    const legacyDir = path.join(os.homedir(), '.heroku');
    if (fs.existsSync(legacyDir)) {
        return legacyDir;
    }
    return path.join(os.homedir(), '.config', 'heroku');
}
function account(name) {
    const basedir = path.join(configDir(), 'accounts');
    const file = fs.readFileSync(path.join(basedir, name), 'utf8');
    const account = (0, yaml_1.parse)(file);
    if (account[':username']) {
        // convert from ruby symbols
        account.username = account[':username'];
        account.password = account[':password'];
        delete account[':username'];
        delete account[':password'];
    }
    return account;
}
function list() {
    const basedir = path.join(configDir(), 'accounts');
    try {
        return fs.readdirSync(basedir)
            .map(name => Object.assign(account(name), { name }));
    }
    catch (_a) {
        return [];
    }
}
exports.list = list;
function current() {
    if (netrc_parser_1.default.machines['api.heroku.com']) {
        const current = list().find(a => a.username === netrc_parser_1.default.machines['api.heroku.com'].login);
        return current && current.name ? current.name : null;
    }
    return null;
}
exports.current = current;
function add(name, username, password) {
    const basedir = path.join(configDir(), 'accounts');
    fs.mkdirSync(basedir, { recursive: true });
    fs.writeFileSync(path.join(basedir, name), (0, yaml_1.stringify)({ username, password }), 'utf8');
    fs.chmodSync(path.join(basedir, name), 0o600);
}
exports.add = add;
function remove(name) {
    const basedir = path.join(configDir(), 'accounts');
    fs.unlinkSync(path.join(basedir, name));
}
exports.remove = remove;
function set(name) {
    const current = account(name);
    netrc_parser_1.default.machines['git.heroku.com'] = {};
    netrc_parser_1.default.machines['api.heroku.com'] = {};
    netrc_parser_1.default.machines['git.heroku.com'].login = current.username;
    netrc_parser_1.default.machines['api.heroku.com'].login = current.username;
    netrc_parser_1.default.machines['git.heroku.com'].password = current.password;
    netrc_parser_1.default.machines['api.heroku.com'].password = current.password;
    netrc_parser_1.default.saveSync();
}
exports.set = set;

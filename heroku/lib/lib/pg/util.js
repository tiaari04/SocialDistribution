"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.databaseNameFromUrl = exports.configVarNamesFromValue = exports.presentCredentialAttachments = exports.formatResponseWithCommands = exports.essentialPlan = exports.legacyEssentialPlan = exports.essentialNumPlan = void 0;
const color_1 = require("@heroku-cli/color");
const core_1 = require("@oclif/core");
const addons_1 = require("../../commands/addons");
const multisort_1 = require("../utils/multisort");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const essentialNumPlan = (addon) => { var _a, _b; return Boolean((_b = (_a = addon === null || addon === void 0 ? void 0 : addon.plan) === null || _a === void 0 ? void 0 : _a.name) === null || _b === void 0 ? void 0 : _b.split(':')[1].match(/^essential/)); };
exports.essentialNumPlan = essentialNumPlan;
const legacyEssentialPlan = (addon) => { var _a, _b; return Boolean((_b = (_a = addon === null || addon === void 0 ? void 0 : addon.plan) === null || _a === void 0 ? void 0 : _a.name) === null || _b === void 0 ? void 0 : _b.split(':')[1].match(/(dev|basic|mini)$/)); };
exports.legacyEssentialPlan = legacyEssentialPlan;
function essentialPlan(addon) {
    return (0, exports.essentialNumPlan)(addon) || (0, exports.legacyEssentialPlan)(addon);
}
exports.essentialPlan = essentialPlan;
function formatResponseWithCommands(response) {
    return response.replace(/`(.*?)`/g, (_, word) => color_1.default.cmd(word));
}
exports.formatResponseWithCommands = formatResponseWithCommands;
function presentCredentialAttachments(app, credAttachments, credentials, cred) {
    const isForeignApp = (attOrAddon) => attOrAddon.app.name === app ? 0 : 1;
    const comparators = [
        (a, b) => {
            const fa = isForeignApp(a);
            const fb = isForeignApp(b);
            return fa < fb ? -1 : (fb < fa ? 1 : 0);
        },
        (a, b) => a.name.localeCompare(b.name),
        (a, b) => { var _a, _b, _c, _d, _e; return (_e = (_b = (_a = a.app) === null || _a === void 0 ? void 0 : _a.name) === null || _b === void 0 ? void 0 : _b.localeCompare((_d = (_c = b.app) === null || _c === void 0 ? void 0 : _c.name) !== null && _d !== void 0 ? _d : '')) !== null && _e !== void 0 ? _e : 0; },
    ];
    credAttachments.sort((0, multisort_1.multiSortCompareFn)(comparators));
    // render each attachment under the credential
    const attLines = credAttachments.map(function (attachment, idx) {
        const isLast = (idx === credAttachments.length - 1);
        return (0, addons_1.renderAttachment)(attachment, app, isLast);
    });
    const rotationLines = [];
    const credentialStore = credentials.find(a => a.name === cred);
    if ((credentialStore === null || credentialStore === void 0 ? void 0 : credentialStore.state) === 'rotating') {
        const formatted = credentialStore === null || credentialStore === void 0 ? void 0 : credentialStore.credentials.map(credential => {
            return {
                user: credential.user,
                state: credential.state,
                connections: credential.connections,
            };
        });
        // eslint-disable-next-line no-eq-null, eqeqeq
        const connectionInformationAvailable = formatted.some(c => c.connections != null);
        if (connectionInformationAvailable) {
            const prefix = '       ';
            rotationLines.push(`${prefix}Usernames currently active for this credential:`);
            core_1.ux.table(formatted, {
                user: {
                    get(row) {
                        return `${prefix}${row.user}`;
                    },
                },
                state: {
                    get(row) {
                        return row.state === 'revoking' ? 'waiting for no connections to be revoked' : row.state;
                    },
                },
                connections: {
                    get(row) {
                        return `${row.connections} connections`;
                    },
                },
            }, {
                'no-header': true,
                printLine(line) {
                    rotationLines.push(line);
                },
            });
        }
    }
    return [cred, ...attLines, ...rotationLines].join('\n');
}
exports.presentCredentialAttachments = presentCredentialAttachments;
const configVarNamesFromValue = (config, value) => {
    const keys = [];
    for (const key of Object.keys(config)) {
        const configVal = config[key];
        if (configVal === value) {
            keys.push(key);
        }
        else if (configVal.startsWith('postgres://')) {
            try {
                const configURL = new URL(configVal);
                const ourURL = new URL(value);
                const components = ['protocol', 'hostname', 'port', 'pathname'];
                if (components.every(component => ourURL[component] === configURL[component])) {
                    keys.push(key);
                }
            }
            catch (_a) {
                // ignore -- this is not a valid URL so not a matching URL
            }
        }
    }
    const comparator = (a, b) => {
        const isDatabaseUrlA = Number(a === 'DATABASE_URL');
        const isDatabaseUrlB = Number(b === 'DATABASE_URL');
        return isDatabaseUrlA < isDatabaseUrlB ? -1 : (isDatabaseUrlB < isDatabaseUrlA ? 1 : 0);
    };
    return keys.sort(comparator);
};
exports.configVarNamesFromValue = configVarNamesFromValue;
const databaseNameFromUrl = (uri, config) => {
    const names = (0, exports.configVarNamesFromValue)(config, uri);
    let name = names.pop();
    while (names.length > 0 && name === 'DATABASE_URL')
        name = names.pop();
    if (name) {
        return color_1.default.configVar(name.replace(/_URL$/, ''));
    }
    const conn = heroku_cli_util_1.utils.pg.DatabaseResolver.parsePostgresConnectionString(uri);
    return `${conn.host}:${conn.port}${conn.pathname}`;
};
exports.databaseNameFromUrl = databaseNameFromUrl;

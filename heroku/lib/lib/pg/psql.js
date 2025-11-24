"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.interactive = exports.execFile = exports.psqlInteractiveOptions = exports.psqlFileOptions = exports.fetchVersion = void 0;
const core_1 = require("@oclif/core");
const debug_1 = require("debug");
const fs = require("fs");
const path = require("node:path");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
async function fetchVersion(db) {
    var _a;
    const psqlService = new heroku_cli_util_1.utils.pg.PsqlService(db);
    const output = await psqlService.execQuery('SHOW server_version', ['-X', '-q']);
    return (_a = output.match(/[0-9]{1,}\.[0-9]{1,}/)) === null || _a === void 0 ? void 0 : _a[0];
}
exports.fetchVersion = fetchVersion;
const pgDebug = (0, debug_1.default)('pg');
function psqlFileOptions(file, dbEnv) {
    pgDebug('Running sql file: %s', file.trim());
    const childProcessOptions = {
        stdio: ['ignore', 'pipe', 'inherit'],
    };
    const psqlArgs = ['-f', file, '--set', 'sslmode=require'];
    return {
        dbEnv,
        psqlArgs,
        childProcessOptions,
    };
}
exports.psqlFileOptions = psqlFileOptions;
function psqlInteractiveOptions(prompt, dbEnv) {
    let psqlArgs = ['--set', `PROMPT1=${prompt}`, '--set', `PROMPT2=${prompt}`];
    const psqlHistoryPath = process.env.HEROKU_PSQL_HISTORY;
    if (psqlHistoryPath) {
        if (fs.existsSync(psqlHistoryPath) && fs.statSync(psqlHistoryPath).isDirectory()) {
            const appLogFile = `${psqlHistoryPath}/${prompt.split(':')[0]}`;
            pgDebug('Logging psql history to %s', appLogFile);
            psqlArgs = psqlArgs.concat(['--set', `HISTFILE=${appLogFile}`]);
        }
        else if (fs.existsSync(path.dirname(psqlHistoryPath))) {
            pgDebug('Logging psql history to %s', psqlHistoryPath);
            psqlArgs = psqlArgs.concat(['--set', `HISTFILE=${psqlHistoryPath}`]);
        }
        else {
            core_1.ux.warn(`HEROKU_PSQL_HISTORY is set but is not a valid path (${psqlHistoryPath})`);
        }
    }
    psqlArgs = psqlArgs.concat(['--set', 'sslmode=require']);
    const childProcessOptions = {
        stdio: 'inherit',
    };
    return {
        dbEnv,
        psqlArgs,
        childProcessOptions,
    };
}
exports.psqlInteractiveOptions = psqlInteractiveOptions;
async function execFile(db, file) {
    const psqlService = new heroku_cli_util_1.utils.pg.PsqlService(db);
    const configs = heroku_cli_util_1.utils.pg.psql.getPsqlConfigs(db);
    const options = psqlFileOptions(file, configs.dbEnv);
    return psqlService.runWithTunnel(configs.dbTunnelConfig, options);
}
exports.execFile = execFile;
async function interactive(db) {
    const psqlService = new heroku_cli_util_1.utils.pg.PsqlService(db);
    const attachmentName = db.attachment.name;
    const prompt = `${db.attachment.app.name}::${attachmentName}%R%# `;
    const configs = heroku_cli_util_1.utils.pg.psql.getPsqlConfigs(db);
    configs.dbEnv.PGAPPNAME = 'psql interactive'; // default was 'psql non-interactive`
    const options = psqlInteractiveOptions(prompt, configs.dbEnv);
    return psqlService.runWithTunnel(configs.dbTunnelConfig, options);
}
exports.interactive = interactive;

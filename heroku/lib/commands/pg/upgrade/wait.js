"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const color_1 = require("@heroku-cli/color");
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const debug_1 = require("debug");
const tsheredoc_1 = require("tsheredoc");
const fetcher_1 = require("../../../lib/pg/fetcher");
const host_1 = require("../../../lib/pg/host");
const notify_1 = require("../../../lib/notify");
const http_call_1 = require("@heroku/http-call");
const nls_1 = require("../../../nls");
const util_1 = require("../../../lib/pg/util");
const wait = (ms) => new Promise(resolve => {
    setTimeout(resolve, ms);
});
class Wait extends command_1.Command {
    async run() {
        const { flags, args } = await this.parse(Wait);
        const { app, 'wait-interval': waitInterval } = flags;
        const dbName = args.database;
        const pgDebug = (0, debug_1.default)('pg');
        const waitFor = async (db) => {
            const interval = (!waitInterval || waitInterval < 0) ? 5 : waitInterval;
            let status;
            let waiting = false;
            let retries = 20;
            const notFoundMessage = 'Waiting to provision...';
            while (true) {
                try {
                    ({ body: status } = await this.heroku.get(`/client/v11/databases/${db.id}/upgrade/wait_status`, { hostname: (0, host_1.default)() }));
                }
                catch (error) {
                    if (error instanceof http_call_1.HTTPError && (!retries || error.statusCode !== 404)) {
                        const httpError = error;
                        pgDebug(httpError);
                        throw httpError;
                    }
                    retries--;
                    status = { 'waiting?': true, message: notFoundMessage };
                }
                let message = (0, util_1.formatResponseWithCommands)(status.message);
                if (status.step)
                    message = (0, tsheredoc_1.default)(`(${status.step}) ${message}`);
                if (status['error?']) {
                    (0, notify_1.default)('error', `${db.name} ${message}`, false);
                    core_1.ux.error(message || '', { exit: 1 });
                }
                if (!status['waiting?']) {
                    if (waiting) {
                        core_1.ux.action.stop(message);
                    }
                    else {
                        core_1.ux.log((0, tsheredoc_1.default)(`Waiting for database ${color_1.default.yellow(db.name)}... ${message}`));
                    }
                    return;
                }
                if (!waiting) {
                    waiting = true;
                    core_1.ux.action.start(`Waiting for database ${color_1.default.yellow(db.name)}`, message);
                }
                core_1.ux.action.status = message;
                await wait(interval * 1000);
            }
        };
        let dbs = [];
        if (dbName) {
            dbs = [await (0, fetcher_1.getAddon)(this.heroku, app, dbName)];
        }
        else {
            core_1.ux.error((0, tsheredoc_1.default)('You must provide a database. Run `--help` for more information on the command.'));
        }
        for (const db of dbs) {
            await waitFor(db);
        }
    }
}
exports.default = Wait;
Wait.topic = 'pg';
Wait.description = 'provides the status of an upgrade and blocks it until the operation is complete';
Wait.flags = {
    'wait-interval': command_1.flags.integer({ description: 'how frequently to poll in seconds (to avoid rate limiting)' }),
    'no-notify': command_1.flags.boolean({ description: 'do not show OS notification' }),
    app: command_1.flags.app({ required: true }),
    remote: command_1.flags.remote(),
};
Wait.examples = [
    (0, tsheredoc_1.default)(`
      # Wait for upgrade to complete with default settings
      $ heroku pg:upgrade:wait postgresql-curved-12345 --app myapp
    `),
    (0, tsheredoc_1.default)(`
      # Wait with custom polling interval
      $ heroku pg:upgrade:wait postgresql-curved-12345 --app myapp --wait-interval 10
    `),
    (0, tsheredoc_1.default)(`
      # Wait without showing OS notifications
      $ heroku pg:upgrade:wait postgresql-curved-12345 --app myapp --no-notify
    `),
];
Wait.args = {
    database: core_1.Args.string({ description: `${(0, nls_1.nls)('pg:database:arg:description')}` }),
};

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const color_1 = require("@heroku-cli/color");
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const tsheredoc_1 = require("tsheredoc");
const fetcher_1 = require("../../../lib/pg/fetcher");
const host_1 = require("../../../lib/pg/host");
const util_1 = require("../../../lib/pg/util");
const confirmCommand_1 = require("../../../lib/confirmCommand");
const nls_1 = require("../../../nls");
class Upgrade extends command_1.Command {
    async run() {
        const { flags, args } = await this.parse(Upgrade);
        const { app, version, confirm } = flags;
        const { database } = args;
        const db = await (0, fetcher_1.getAddon)(this.heroku, app, database);
        if ((0, util_1.legacyEssentialPlan)(db))
            core_1.ux.error(`You can only use ${color_1.default.cmd('pg:upgrade:*')} commands on Essential-* and higher plans.`);
        const versionPhrase = version ? (0, tsheredoc_1.default)(`Postgres version ${version}`) : (0, tsheredoc_1.default)('the latest supported Postgres version');
        const { body: replica } = await this.heroku.get(`/client/v11/databases/${db.id}`, { hostname: (0, host_1.default)() });
        if ((0, util_1.essentialNumPlan)(db)) {
            await (0, confirmCommand_1.default)(app, confirm, (0, tsheredoc_1.default)(`
        Destructive action
        You're upgrading ${color_1.default.addon(db.name)} to ${versionPhrase}.

        You can't undo this action.
      `));
        }
        else if (replica.following) {
            const { body: configVars } = await this.heroku.get(`/apps/${app}/config-vars`);
            const origin = (0, util_1.databaseNameFromUrl)(replica.following, configVars);
            await (0, confirmCommand_1.default)(app, confirm, (0, tsheredoc_1.default)(`
        Destructive action
        You're upgrading ${color_1.default.addon(db.name)} to ${versionPhrase}. The database will stop following ${origin} and become writable.

        You can't undo this action.
      `));
        }
        else {
            await (0, confirmCommand_1.default)(app, confirm, (0, tsheredoc_1.default)(`
        Destructive action
        You're upgrading the Postgres version on ${color_1.default.addon(db.name)}. This action also upgrades any followers on the database.

        You can't undo this action.
      `));
        }
        try {
            const data = { version };
            core_1.ux.action.start(`Starting upgrade on ${color_1.default.addon(db.name)}`);
            const response = await this.heroku.post(`/client/v11/databases/${db.id}/upgrade/run`, { hostname: (0, host_1.default)(), body: data });
            core_1.ux.action.stop((0, tsheredoc_1.default)(`done\n${(0, util_1.formatResponseWithCommands)(response.body.message)}`));
        }
        catch (error) {
            if (error instanceof Error && 'body' in error) {
                const response = error;
                core_1.ux.error((0, tsheredoc_1.default)(`${(0, util_1.formatResponseWithCommands)(response.body.message)}\n\nError ID: ${response.body.id}`));
            }
            else {
                throw error;
            }
        }
    }
}
exports.default = Upgrade;
Upgrade.topic = 'pg';
Upgrade.description = (0, tsheredoc_1.default)(`
    starts a Postgres version upgrade

    On Essential-tier databases, this command upgrades the database's Postgres version.

    On Standard-tier and higher leader databases, this command runs a previously scheduled Postgres version upgrade. You must run ${color_1.default.cmd('pg:upgrade:prepare')} before this command to schedule a version upgrade.

    On follower databases, this command unfollows the leader database before upgrading the follower's Postgres version.
    `);
Upgrade.examples = [
    (0, tsheredoc_1.default) `
      # Upgrade an Essential-tier database to a specific version
      $ heroku pg:upgrade:run postgresql-curved-12345 --version 14 --app myapp
    `,
    (0, tsheredoc_1.default) `
      # Upgrade a Standard-tier follower database to the latest supported version
      $ heroku pg:upgrade:run HEROKU_POSTGRESQL_BLUE_URL --app myapp
    `,
    (0, tsheredoc_1.default) `
      # Run a previously scheduled upgrade on a Standard-tier leader database
      $ heroku pg:upgrade:run DATABASE_URL --app myapp
    `,
];
Upgrade.flags = {
    confirm: command_1.flags.string({ char: 'c' }),
    version: command_1.flags.string({ char: 'v', description: 'Postgres version to upgrade to' }),
    app: command_1.flags.app({ required: true }),
    remote: command_1.flags.remote({ char: 'r' }),
};
Upgrade.args = {
    database: core_1.Args.string({ description: `${(0, nls_1.nls)('pg:database:arg:description')} ${(0, nls_1.nls)('pg:database:arg:description:default:suffix')}` }),
};

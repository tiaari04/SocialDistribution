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
            core_1.ux.error(`You can only use ${color_1.default.cmd('heroku pg:upgrade')} on Essential-tier databases and follower databases on Standard-tier and higher plans.`);
        const versionPhrase = version ? (0, tsheredoc_1.default)(`Postgres version ${version}`) : (0, tsheredoc_1.default)('the latest supported Postgres version');
        const { body: replica } = await this.heroku.get(`/client/v11/databases/${db.id}`, { hostname: (0, host_1.default)() });
        if (replica.following) {
            const { body: configVars } = await this.heroku.get(`/apps/${app}/config-vars`);
            const origin = (0, util_1.databaseNameFromUrl)(replica.following, configVars);
            await (0, confirmCommand_1.default)(app, confirm, (0, tsheredoc_1.default)(`
        We're deprecating this command. To upgrade your database's Postgres version, use the new ${color_1.default.cmd('pg:upgrade:*')} subcommands. See https://devcenter.heroku.com/changelog-items/3179.

        Destructive action
        You're upgrading ${color_1.default.addon(db.name)} to ${versionPhrase}. The database will stop following ${origin} and become writable.

        You can't undo this action.
      `));
        }
        else if ((0, util_1.essentialNumPlan)(db)) {
            await (0, confirmCommand_1.default)(app, confirm, (0, tsheredoc_1.default)(`
        We're deprecating this command. To upgrade your database's Postgres version, use the new ${color_1.default.cmd('pg:upgrade:*')} subcommands. See https://devcenter.heroku.com/changelog-items/3179.

        Destructive action
        You're upgrading ${color_1.default.addon(db.name)} to ${versionPhrase}.

        You can't undo this action.
      `));
        }
        else {
            core_1.ux.warn((0, tsheredoc_1.default)(`
        We're deprecating this command. To upgrade your database's Postgres version, use the new ${color_1.default.cmd('pg:upgrade:*')} subcommands. See https://devcenter.heroku.com/changelog-items/3179.`));
            core_1.ux.error(`You can only use ${color_1.default.cmd('heroku pg:upgrade')} on Essential-tier databases and follower databases on Standard-tier and higher plans.`);
        }
        try {
            const data = { version };
            core_1.ux.action.start(`Starting upgrade on ${color_1.default.addon(db.name)}`);
            const response = await this.heroku.post(`/client/v11/databases/${db.id}/upgrade`, { hostname: (0, host_1.default)(), body: data });
            core_1.ux.action.stop((0, tsheredoc_1.default)(`done\n${(0, util_1.formatResponseWithCommands)(response.body.message)}`));
        }
        catch (error) {
            const response = error;
            core_1.ux.error((0, tsheredoc_1.default)(`${(0, util_1.formatResponseWithCommands)(response.body.message)}\n\nError ID: ${response.body.id}`));
        }
    }
}
exports.default = Upgrade;
Upgrade.topic = 'pg';
Upgrade.description = (0, tsheredoc_1.default)(`
    We're deprecating this command. To upgrade your database's Postgres version, use the new ${color_1.default.cmd('pg:upgrade:*')} subcommands. See https://devcenter.heroku.com/changelog-items/3179.
    
    For an Essential-tier plan, this command upgrades the database's Postgres version. For a Standard-tier and higher plan, this command unfollows the leader database before upgrading the Postgres version.
    `);
Upgrade.flags = {
    confirm: command_1.flags.string({ char: 'c' }),
    version: command_1.flags.string({ char: 'v', description: 'Postgres version to upgrade to' }),
    app: command_1.flags.app({ required: true }),
    remote: command_1.flags.remote(),
};
Upgrade.args = {
    database: core_1.Args.string({ description: `${(0, nls_1.nls)('pg:database:arg:description')} ${(0, nls_1.nls)('pg:database:arg:description:default:suffix')}` }),
};

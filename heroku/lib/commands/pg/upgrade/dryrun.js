"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const color_1 = require("@heroku-cli/color");
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const tsheredoc_1 = require("tsheredoc");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const util_1 = require("../../../lib/pg/util");
const confirmCommand_1 = require("../../../lib/confirmCommand");
const nls_1 = require("../../../nls");
class Upgrade extends command_1.Command {
    async run() {
        const { flags, args } = await this.parse(Upgrade);
        const { app, version, confirm } = flags;
        const { database } = args;
        const dbResolver = new heroku_cli_util_1.utils.pg.DatabaseResolver(this.heroku);
        const { addon: db } = await dbResolver.getAttachment(app, database);
        if ((0, util_1.legacyEssentialPlan)(db))
            core_1.ux.error(`You can only use ${color_1.default.cmd('pg:upgrade:*')} commands on Essential-* and higher plans.`);
        if ((0, util_1.essentialNumPlan)(db))
            core_1.ux.error(`You can't use ${color_1.default.cmd('pg:upgrade:dryrun')} on Essential-tier databases. You can only use this command on Standard-tier and higher leader databases.`);
        const versionPhrase = version ? (0, tsheredoc_1.default)(`Postgres version ${version}`) : (0, tsheredoc_1.default)('the latest supported Postgres version');
        const { body: replica } = await this.heroku.get(`/client/v11/databases/${db.id}`, { hostname: heroku_cli_util_1.utils.pg.host() });
        if (replica.following)
            core_1.ux.error(`You can't use ${color_1.default.cmd('pg:upgrade:dryrun')} on follower databases. You can only use this command on Standard-tier and higher leader databases.`);
        await (0, confirmCommand_1.default)(app, confirm, (0, tsheredoc_1.default)(`
        This command starts a test upgrade for ${color_1.default.addon(db.name)} to ${versionPhrase}.
    `));
        try {
            const data = { version };
            core_1.ux.action.start(`Starting a test upgrade on ${color_1.default.addon(db.name)}`);
            const response = await this.heroku.post(`/client/v11/databases/${db.id}/upgrade/dry_run`, { hostname: heroku_cli_util_1.utils.pg.host(), body: data });
            core_1.ux.action.stop('done\n' + (0, util_1.formatResponseWithCommands)(response.body.message));
        }
        catch (error) {
            const response = error;
            core_1.ux.error((0, util_1.formatResponseWithCommands)(response.body.message) + `\n\nError ID: ${response.body.id}`);
        }
    }
}
exports.default = Upgrade;
Upgrade.topic = 'pg';
Upgrade.description = (0, tsheredoc_1.default)(`
    simulates a Postgres version upgrade on a Standard-tier and higher leader database by creating and upgrading a follower database. Heroku sends the results of the test upgrade via email.
  `);
Upgrade.flags = {
    confirm: command_1.flags.string({ char: 'c' }),
    version: command_1.flags.string({ char: 'v', description: 'Postgres version to upgrade to' }),
    app: command_1.flags.app({ required: true }),
};
Upgrade.args = {
    database: core_1.Args.string({ description: `${(0, nls_1.nls)('pg:database:arg:description')} ${(0, nls_1.nls)('pg:database:arg:description:default:suffix')}` }),
};

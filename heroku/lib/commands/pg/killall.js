"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const nls_1 = require("../../nls");
class Killall extends command_1.Command {
    async run() {
        const { flags, args } = await this.parse(Killall);
        const { app } = flags;
        core_1.ux.action.start('Terminating connections for all credentials');
        const dbResolver = new heroku_cli_util_1.utils.pg.DatabaseResolver(this.heroku);
        const { addon } = await dbResolver.getAttachment(app, args.database);
        await this.heroku.post(`/client/v11/databases/${addon.id}/connection_reset`, { hostname: heroku_cli_util_1.utils.pg.host() });
        core_1.ux.action.stop();
    }
}
exports.default = Killall;
Killall.topic = 'pg';
Killall.description = 'terminates all connections for all credentials';
Killall.flags = {
    app: command_1.flags.app({ required: true }),
    remote: command_1.flags.remote(),
};
Killall.args = {
    database: core_1.Args.string({ description: `${(0, nls_1.nls)('pg:database:arg:description')} ${(0, nls_1.nls)('pg:database:arg:description:default:suffix')}` }),
};

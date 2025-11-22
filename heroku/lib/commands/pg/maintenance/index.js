"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const util_1 = require("../../../lib/pg/util");
const nls_1 = require("../../../nls");
class Index extends command_1.Command {
    async run() {
        const { flags, args } = await this.parse(Index);
        const { app } = flags;
        const { database } = args;
        const dbResolver = new heroku_cli_util_1.utils.pg.DatabaseResolver(this.heroku);
        const { addon: db } = await dbResolver.getAttachment(app, database);
        if ((0, util_1.essentialPlan)(db))
            core_1.ux.error('pg:maintenance isn’t available for Essential-tier databases.');
        const { body: info } = await this.heroku.get(`/client/v11/databases/${db.id}/maintenance`, { hostname: heroku_cli_util_1.utils.pg.host() });
        core_1.ux.log(info.message);
    }
}
exports.default = Index;
Index.topic = 'pg';
Index.description = 'show current maintenance information';
Index.flags = {
    app: command_1.flags.app({ required: true }),
    remote: command_1.flags.remote(),
};
Index.args = {
    database: core_1.Args.string({ description: `${(0, nls_1.nls)('pg:database:arg:description')} ${(0, nls_1.nls)('pg:database:arg:description:default:suffix')}` }),
};

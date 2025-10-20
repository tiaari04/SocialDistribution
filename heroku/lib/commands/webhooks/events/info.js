"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const base_1 = require("../../../lib/webhooks/base");
class Info extends base_1.default {
    async run() {
        const { flags, args } = await this.parse(Info);
        const { path } = this.webhookType(flags);
        core_1.ux.warn('heroku webhooks:event:info is deprecated, please use heroku webhooks:deliveries:info');
        const { body: webhookEvent } = await this.webhooksClient.get(`${path}/webhook-events/${args.id}`);
        const obj = {
            payload: JSON.stringify(webhookEvent.payload, null, 2),
        };
        heroku_cli_util_1.hux.styledHeader(webhookEvent.id);
        heroku_cli_util_1.hux.styledObject(obj);
    }
}
exports.default = Info;
Info.description = 'info for a webhook event on an app';
Info.examples = [
    '$ heroku webhooks:events:info 99999999-9999-9999-9999-999999999999',
];
Info.flags = {
    app: command_1.flags.app(),
    remote: command_1.flags.remote(),
    pipeline: command_1.flags.pipeline({ char: 'p', description: 'pipeline on which to list', hidden: true }),
};
Info.args = {
    id: core_1.Args.string({ required: true, description: 'ID of the webhook event' }),
};

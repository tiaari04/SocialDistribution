"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const base_1 = require("../../../lib/webhooks/base");
class DeliveriesInfo extends base_1.default {
    async run() {
        const { flags, args } = await this.parse(DeliveriesInfo);
        const { path } = this.webhookType(flags);
        const { body: delivery } = await this.webhooksClient.get(`${path}/webhook-deliveries/${args.id}`);
        const { body: event } = await this.webhooksClient.get(`${path}/webhook-events/${delivery.event.id}`);
        const obj = {
            Created: delivery.created_at,
            Event: delivery.event.id,
            Webhook: delivery.webhook.id,
            Status: delivery.status,
            Include: delivery.event.include,
            Level: delivery.webhook.level,
            Attempts: delivery.num_attempts,
            Code: delivery.last_attempt && delivery.last_attempt.code,
            Error: delivery.last_attempt && delivery.last_attempt.error_class,
            'Next Attempt': delivery.next_attempt_at,
        };
        heroku_cli_util_1.hux.styledHeader(delivery.id);
        heroku_cli_util_1.hux.styledObject(obj);
        heroku_cli_util_1.hux.styledHeader('Event Payload');
        heroku_cli_util_1.hux.styledJSON(event.payload);
    }
}
exports.default = DeliveriesInfo;
DeliveriesInfo.description = 'info for a webhook event on an app';
DeliveriesInfo.examples = [
    '$ heroku webhooks:deliveries:info 99999999-9999-9999-9999-999999999999',
];
DeliveriesInfo.flags = {
    app: command_1.flags.app(),
    remote: command_1.flags.remote(),
    pipeline: command_1.flags.pipeline({ char: 'p', description: 'pipeline on which to list', hidden: true }),
};
DeliveriesInfo.args = {
    id: core_1.Args.string({ required: true, description: 'ID of the webhook event' }),
};

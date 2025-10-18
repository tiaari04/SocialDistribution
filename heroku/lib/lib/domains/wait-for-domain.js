"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const color_1 = require("@heroku-cli/color");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const spinner_1 = require("@oclif/core/lib/cli-ux/action/spinner");
async function waitForDomain(app, heroku, domain) {
    const action = new spinner_1.default();
    action.start(`Waiting for ${color_1.color.green(domain.hostname || 'domain')}`);
    while (domain.status === 'pending') {
        await heroku_cli_util_1.hux.wait(5000);
        const { body: updatedDomain } = await heroku.get(`/apps/${app}/domains/${domain.id}`);
        domain = updatedDomain;
    }
    action.stop();
    if (domain.status === 'succeeded' || domain.status === 'none')
        return;
    throw new Error(`The domain creation finished with status ${domain.status}`);
}
exports.default = waitForDomain;

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
async function getCISettings(yes, organization) {
    const settings = {
        ci: true,
        organization: undefined,
    };
    if (yes) {
        delete settings.organization;
        return settings;
    }
    settings.ci = await heroku_cli_util_1.hux.confirm('Enable automatic Heroku CI test runs?');
    if (settings.ci && organization) {
        settings.organization = organization;
    }
    return settings;
}
exports.default = getCISettings;

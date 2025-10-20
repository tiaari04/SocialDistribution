"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const accounts_1 = require("../../lib/accounts/accounts");
const color_1 = require("@heroku-cli/color");
class Current extends command_1.Command {
    async run() {
        const account = (0, accounts_1.current)();
        if (account) {
            heroku_cli_util_1.hux.styledHeader(`Current account is ${account}`);
        }
        else {
            core_1.ux.error(`You haven't set an account. Run ${color_1.default.cmd('heroku accounts:add <account-name>')} to add an account to your cache or ${color_1.default.cmd('heroku accounts:set <account-name>')} to set the current account.`);
        }
    }
}
exports.default = Current;
Current.description = 'display the current Heroku account';
Current.example = 'heroku accounts:current';

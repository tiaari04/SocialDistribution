"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const accounts_1 = require("../../lib/accounts/accounts");
class AccountsIndex extends command_1.Command {
    async run() {
        const accounts = (0, accounts_1.list)();
        if (accounts.length === 0) {
            core_1.ux.error('You don\'t have any accounts in your cache.');
        }
        for (const account of accounts) {
            if (account.name === (0, accounts_1.current)()) {
                core_1.ux.log(`* ${account.name}`);
            }
            else {
                core_1.ux.log(`  ${account.name}`);
            }
        }
    }
}
exports.default = AccountsIndex;
AccountsIndex.description = 'list the Heroku accounts in your cache';
AccountsIndex.example = 'heroku accounts';

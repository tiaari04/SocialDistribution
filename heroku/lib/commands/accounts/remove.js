"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const accounts_1 = require("../../lib/accounts/accounts");
class Remove extends command_1.Command {
    async run() {
        const { args } = await this.parse(Remove);
        const { name } = args;
        if (!(0, accounts_1.list)().some(a => a.name === name)) {
            core_1.ux.error(`${name} doesn't exist in your accounts cache.`);
        }
        if ((0, accounts_1.current)() === name) {
            core_1.ux.error(`${name} is the current account.`);
        }
        (0, accounts_1.remove)(name);
    }
}
exports.default = Remove;
Remove.description = 'remove a Heroku account from your cache';
Remove.args = {
    name: core_1.Args.string({ description: 'name of Heroku account to remove', required: true }),
};
Remove.example = 'heroku accounts:remove my-account';

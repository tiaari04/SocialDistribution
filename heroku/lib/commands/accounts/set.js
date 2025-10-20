"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const accounts_1 = require("../../lib/accounts/accounts");
class Set extends command_1.Command {
    async run() {
        const { args } = await this.parse(Set);
        const { name } = args;
        if (!(0, accounts_1.list)().some(a => a.name === name)) {
            core_1.ux.error(`${name} does not exist in your accounts cache.`);
        }
        (0, accounts_1.set)(name);
    }
}
exports.default = Set;
Set.description = 'set the current Heroku account from your cache';
Set.args = {
    name: core_1.Args.string({ description: 'name of account to set', required: true }),
};
Set.example = 'heroku accounts:set my-account';

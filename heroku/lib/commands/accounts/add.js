"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const accounts_1 = require("../../lib/accounts/accounts");
class Add extends command_1.Command {
    async run() {
        const { args } = await this.parse(Add);
        const { name } = args;
        const logInMessage = 'You must be logged in to run this command.';
        if ((0, accounts_1.list)().some(a => a.name === name)) {
            core_1.ux.error(`${name} already exists`);
        }
        const { body: account } = await this.heroku.get('/account');
        const email = account.email || '';
        const token = this.heroku.auth || '';
        if (token === '') {
            core_1.ux.error(logInMessage);
        }
        if (email === '') {
            core_1.ux.error(logInMessage);
        }
        (0, accounts_1.add)(name, email, token);
    }
}
exports.default = Add;
Add.description = 'add a Heroku account to your cache';
Add.args = {
    name: core_1.Args.string({ description: 'name of Heroku account to add', required: true }),
};
Add.example = 'heroku accounts:add my-account';

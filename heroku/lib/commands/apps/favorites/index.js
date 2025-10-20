"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const command_1 = require("@heroku-cli/command");
class Index extends command_1.Command {
    async run() {
        const { flags } = await this.parse(Index);
        const { body: favorites } = await this.heroku.get('/favorites?type=app', { hostname: 'particleboard.heroku.com' });
        if (flags.json) {
            heroku_cli_util_1.hux.styledJSON(favorites);
        }
        else {
            heroku_cli_util_1.hux.styledHeader('Favorited Apps');
            for (const f of favorites) {
                core_1.ux.log(f.resource_name);
            }
        }
    }
}
exports.default = Index;
Index.description = 'list favorited apps';
Index.topic = 'apps';
Index.flags = {
    json: command_1.flags.boolean({ char: 'j', description: 'output in json format' }),
};

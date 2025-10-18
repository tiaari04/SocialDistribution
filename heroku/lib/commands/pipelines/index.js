"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
class Pipelines extends command_1.Command {
    async run() {
        const { flags } = await this.parse(Pipelines);
        const { body: pipelines } = await this.heroku.get('/pipelines');
        if (flags.json) {
            heroku_cli_util_1.hux.styledJSON(pipelines);
        }
        else {
            heroku_cli_util_1.hux.styledHeader('My Pipelines');
            for (const pipeline of pipelines) {
                core_1.ux.log(pipeline.name);
            }
        }
    }
}
exports.default = Pipelines;
Pipelines.description = 'list pipelines you have access to';
Pipelines.examples = [
    '$ heroku pipelines',
];
Pipelines.flags = {
    json: command_1.flags.boolean({ description: 'output in json format' }),
};

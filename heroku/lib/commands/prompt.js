"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const core_1 = require("@oclif/core");
class Prompt extends core_1.Command {
    async run() {
        core_1.ux.warn('use `heroku <COMMAND> --prompt` to interactively prompt for command arguments and flags');
    }
}
exports.default = Prompt;
Prompt.description = 'interactively prompt for command arguments and flags';
Prompt.hidden = true;
Prompt.examples = [
    '$ heroku apps:info --prompt',
    '$ heroku config:set --prompt',
];
Prompt.strict = false;

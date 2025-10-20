"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const core_1 = require("@oclif/core");
class Repl extends core_1.Command {
    async run() {
        core_1.ux.warn('use `heroku --repl` to enter an interactive REPL session to run Heroku CLI commands');
    }
}
exports.default = Repl;
Repl.description = 'enter an interactive REPL session to run Heroku CLI commands';
Repl.hidden = true;
Repl.examples = [
    '$ heroku --repl',
];

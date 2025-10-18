"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const node_child_process_1 = require("node:child_process");
const path_1 = require("path");
class MCPStart extends command_1.Command {
    async run() {
        const serverPath = (0, path_1.join)(require.resolve('@heroku/mcp-server'), '../../bin/heroku-mcp-server.mjs');
        const server = MCPStart.spawn('node', [serverPath], {
            stdio: ['pipe', 'pipe', 'pipe'],
            shell: true,
        });
        // Pipe all stdio streams
        process.stdin.pipe(server.stdin);
        server.stdout.pipe(process.stdout);
        server.stderr.pipe(process.stderr);
        // Handle process termination
        process.on('SIGINT', () => {
            server.kill('SIGINT');
        });
        process.on('SIGTERM', () => {
            server.kill('SIGTERM');
        });
        return server;
    }
}
exports.default = MCPStart;
MCPStart.description = 'starts the Heroku platform MCP server in stdio mode';
MCPStart.hidden = true;
MCPStart.flags = {
    help: command_1.flags.help({ char: 'h' }),
};
MCPStart.spawn = node_child_process_1.spawn;

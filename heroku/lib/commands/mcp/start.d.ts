/// <reference types="node" />
import { Command } from '@heroku-cli/command';
import { spawn as cpSpawn } from 'node:child_process';
export default class MCPStart extends Command {
    static description: string;
    static hidden: boolean;
    static flags: {
        help: import("@oclif/core/lib/interfaces").BooleanFlag<void>;
    };
    static spawn: typeof cpSpawn;
    run(): Promise<import("child_process").ChildProcessWithoutNullStreams>;
}

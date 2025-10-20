import { Command } from '@oclif/core';
export default class Repl extends Command {
    static description: string;
    static hidden: boolean;
    static examples: string[];
    run(): Promise<void>;
}

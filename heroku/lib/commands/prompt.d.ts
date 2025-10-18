import { Command } from '@oclif/core';
export default class Prompt extends Command {
    static description: string;
    static hidden: boolean;
    static examples: string[];
    static strict: boolean;
    run(): Promise<void>;
}

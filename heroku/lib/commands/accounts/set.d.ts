import { Command } from '@heroku-cli/command';
export default class Set extends Command {
    static description: string;
    static args: {
        name: import("@oclif/core/lib/interfaces/parser").Arg<string, Record<string, unknown>>;
    };
    static example: string;
    run(): Promise<void>;
}

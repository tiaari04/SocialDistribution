import { Command } from '@heroku-cli/command';
export default class Current extends Command {
    static description: string;
    static example: string;
    run(): Promise<void>;
}

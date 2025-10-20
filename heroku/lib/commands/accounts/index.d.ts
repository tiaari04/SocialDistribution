import { Command } from '@heroku-cli/command';
export default class AccountsIndex extends Command {
    static description: string;
    static example: string;
    run(): Promise<void>;
}

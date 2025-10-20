import { Command } from '@heroku-cli/command';
export default class UsageAddons extends Command {
    static topic: string;
    static description: string;
    static flags: {
        app: import("@oclif/core/lib/interfaces").OptionFlag<string | undefined, import("@oclif/core/lib/interfaces/parser").CustomOptions>;
        team: import("@oclif/core/lib/interfaces").OptionFlag<string | undefined, import("@oclif/core/lib/interfaces/parser").CustomOptions>;
    };
    private displayAppUsage;
    private fetchAndDisplayAppUsageData;
    private fetchAndDisplayTeamUsageData;
    private getAppInfoFromTeamAddons;
    run(): Promise<void>;
}

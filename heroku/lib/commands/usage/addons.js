"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const color_1 = require("@heroku-cli/color");
class UsageAddons extends command_1.Command {
    displayAppUsage(app, usageAddons, appAddons) {
        const metersArray = usageAddons.flatMap(addon => Object.entries(addon.meters).map(([label, data]) => ({
            label,
            quantity: data.quantity,
            addonId: addon.id,
        })));
        heroku_cli_util_1.hux.styledHeader(`Usage for ${color_1.default.app(app)}`);
        heroku_cli_util_1.hux.table(metersArray, {
            'Add-on': {
                get: row => {
                    const matchingAddon = appAddons.find(a => a.id === row.addonId);
                    return (matchingAddon === null || matchingAddon === void 0 ? void 0 : matchingAddon.name) || row.addonId;
                },
            },
            Meter: {
                get: row => row.label,
            },
            Quantity: {
                get: row => row.quantity,
            },
        });
    }
    async fetchAndDisplayAppUsageData(app, team) {
        let usageData;
        let appAddons;
        core_1.ux.action.start('Gathering usage data');
        if (team) {
            [{ body: usageData }, { body: appAddons }] = await Promise.all([
                this.heroku.get(`/teams/${team}/apps/${app}/usage`, {
                    headers: {
                        Accept: 'application/vnd.heroku+json; version=3.sdk',
                    },
                }),
                this.heroku.get(`/apps/${app}/addons`),
            ]);
        }
        else {
            [{ body: usageData }, { body: appAddons }] = await Promise.all([
                this.heroku.get(`/apps/${app}/usage`, {
                    headers: {
                        Accept: 'application/vnd.heroku+json; version=3.sdk',
                    },
                }),
                this.heroku.get(`/apps/${app}/addons`),
            ]);
        }
        core_1.ux.action.stop();
        core_1.ux.log();
        const usageAddons = usageData.addons;
        if (usageAddons.length === 0) {
            core_1.ux.log(`No usage found for app ${color_1.default.app(app)}`);
            return;
        }
        this.displayAppUsage(app, usageAddons, appAddons);
    }
    async fetchAndDisplayTeamUsageData(team) {
        core_1.ux.action.start(`Gathering usage data for ${color_1.default.magenta(team)}`);
        const [{ body: usageData }, { body: teamAddons }] = await Promise.all([
            this.heroku.get(`/teams/${team}/usage`, {
                headers: {
                    Accept: 'application/vnd.heroku+json; version=3.sdk',
                },
            }),
            this.heroku.get(`/teams/${team}/addons`),
        ]);
        core_1.ux.action.stop();
        core_1.ux.log();
        if (!usageData.apps || usageData.apps.length === 0) {
            core_1.ux.log(`No usage found for team ${color_1.default.magenta(team)}`);
            return;
        }
        const appInfoArray = this.getAppInfoFromTeamAddons(teamAddons);
        // Display usage for each app
        usageData.apps.forEach((app) => {
            const appInfo = appInfoArray.find(info => info.id === app.id);
            this.displayAppUsage((appInfo === null || appInfo === void 0 ? void 0 : appInfo.name) || app.id, app.addons, teamAddons);
            core_1.ux.log();
        });
    }
    getAppInfoFromTeamAddons(teamAddons) {
        const appInfoMap = new Map();
        teamAddons.forEach(addon => {
            if (addon.app && addon.app.id && addon.app.name) {
                appInfoMap.set(addon.app.id, addon.app.name);
            }
        });
        return Array.from(appInfoMap.entries()).map(([id, name]) => ({
            id,
            name,
        }));
    }
    async run() {
        const { flags } = await this.parse(UsageAddons);
        const { app, team } = flags;
        if (!app && !team) {
            core_1.ux.error('Specify an app with --app or a team with --team');
        }
        if (app) {
            await this.fetchAndDisplayAppUsageData(app, team);
        }
        else if (team) {
            await this.fetchAndDisplayTeamUsageData(team);
        }
    }
}
exports.default = UsageAddons;
UsageAddons.topic = 'usage';
UsageAddons.description = 'list usage for metered add-ons attached to an app or apps within a team';
UsageAddons.flags = {
    app: command_1.flags.string({ char: 'a', description: 'app to list metered add-ons usage for' }),
    team: command_1.flags.team({ description: 'team to list metered add-ons usage for' }),
};

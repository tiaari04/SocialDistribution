"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const color_1 = require("@heroku-cli/color");
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const util_1 = require("@oclif/core/lib/util");
const date_fns_1 = require("date-fns");
const http_call_1 = require("@heroku/http-call");
const util_2 = require("../lib/status/util");
const errorMessage = 'Heroku platform status is unavailable at this time. Refer to https://status.salesforce.com/products/Heroku or try again later.';
const printStatus = (status) => {
    const colorize = color_1.default[status];
    let message = (0, util_1.capitalize)(status);
    if (status === 'green') {
        message = 'No known issues at this time.';
    }
    return colorize(message);
};
const getTrustStatus = async () => {
    const trustHost = process.env.SF_TRUST_STAGING ? 'https://status-api-stg.test.edgekey.net/v1' : 'https://api.status.salesforce.com/v1';
    const currentDateTime = new Date(Date.now()).toISOString();
    let instances = [];
    let activeIncidents = [];
    let maintenances = [];
    let localizations = [];
    try {
        const [instanceResponse, activeIncidentsResponse, maintenancesResponse, localizationsResponse] = await Promise.all([
            http_call_1.default.get(`${trustHost}/instances?products=Heroku`),
            http_call_1.default.get(`${trustHost}/incidents/active`),
            http_call_1.default.get(`${trustHost}/maintenances?startTime=${currentDateTime}&limit=10&offset=0&product=Heroku&locale=en`),
            http_call_1.default.get(`${trustHost}/localizations?locale=en`),
        ]);
        instances = instanceResponse.body;
        activeIncidents = activeIncidentsResponse.body;
        maintenances = maintenancesResponse.body;
        localizations = localizationsResponse.body;
    }
    catch (_a) {
        core_1.ux.error(errorMessage, { exit: 1 });
    }
    return formatTrustResponse(instances, activeIncidents, maintenances, localizations);
};
const determineIncidentSeverity = (incidents) => {
    const severityArray = [];
    incidents.forEach(incident => {
        incident.IncidentImpacts.forEach(impact => {
            if (!impact.endTime && impact.severity) {
                severityArray.push(impact.severity);
            }
        });
    });
    if (severityArray.includes('major'))
        return 'red';
    if (severityArray.includes('minor'))
        return 'yellow';
    return 'green';
};
const formatTrustResponse = (instances, activeIncidents, maintenances, localizations) => {
    const systemStatus = [];
    const incidents = [];
    const scheduled = [];
    const instanceKeyArray = new Set(instances.map(instance => instance.key));
    const herokuActiveIncidents = activeIncidents.filter(incident => {
        return incident.instanceKeys.some(key => instanceKeyArray.has(key));
    });
    const toolsIncidents = herokuActiveIncidents.filter(incident => {
        const tools = ['TOOLS', 'Tools', 'CLI', 'Dashboard', 'Platform API'];
        return tools.some(tool => incident.serviceKeys.includes(tool));
    });
    const appsIncidents = herokuActiveIncidents.filter(incident => {
        return incident.serviceKeys.includes('HerokuApps') || incident.serviceKeys.includes('Apps');
    });
    const dataIncidents = herokuActiveIncidents.filter(incident => {
        return incident.serviceKeys.includes('HerokuData') || incident.serviceKeys.includes('Data');
    });
    if (appsIncidents.length > 0) {
        const severity = determineIncidentSeverity(appsIncidents);
        systemStatus.push({ system: 'Apps', status: severity });
        incidents.push(...appsIncidents);
    }
    else {
        systemStatus.push({ system: 'Apps', status: 'green' });
    }
    if (dataIncidents.length > 0) {
        const severity = determineIncidentSeverity(dataIncidents);
        systemStatus.push({ system: 'Data', status: severity });
        incidents.push(...dataIncidents);
    }
    else {
        systemStatus.push({ system: 'Data', status: 'green' });
    }
    if (toolsIncidents.length > 0) {
        const severity = determineIncidentSeverity(toolsIncidents);
        systemStatus.push({ system: 'Tools', status: severity });
        incidents.push(...toolsIncidents);
    }
    else {
        systemStatus.push({ system: 'Tools', status: 'green' });
    }
    if (maintenances.length > 0)
        scheduled.push(...maintenances);
    if (incidents.length > 0) {
        incidents.forEach(incident => {
            incident.IncidentEvents.forEach(event => {
                var _a;
                event.localizedType = (_a = localizations.find((l) => l.modelKey === event.type)) === null || _a === void 0 ? void 0 : _a.text;
            });
        });
    }
    return {
        status: systemStatus,
        incidents,
        scheduled,
    };
};
class Status extends core_1.Command {
    async run() {
        var _a;
        const { flags } = await this.parse(Status);
        const herokuApiPath = '/api/v4/current-status';
        let herokuStatus;
        let formattedTrustStatus;
        if (process.env.TRUST_ONLY) {
            formattedTrustStatus = await getTrustStatus();
        }
        else {
            try {
                // Try calling the Heroku status API first
                const herokuHost = process.env.HEROKU_STATUS_HOST || 'https://status.heroku.com';
                const herokuStatusResponse = await http_call_1.default.get(herokuHost + herokuApiPath);
                herokuStatus = herokuStatusResponse.body;
            }
            catch (_b) {
                // If the Heroku status API call fails, call the SF Trust API
                formattedTrustStatus = await getTrustStatus();
            }
        }
        if (!herokuStatus && !formattedTrustStatus)
            core_1.ux.error(errorMessage, { exit: 1 });
        if (flags.json) {
            heroku_cli_util_1.hux.styledJSON(herokuStatus !== null && herokuStatus !== void 0 ? herokuStatus : formattedTrustStatus);
            return;
        }
        const systemStatus = herokuStatus ? herokuStatus.status : formattedTrustStatus === null || formattedTrustStatus === void 0 ? void 0 : formattedTrustStatus.status;
        if (systemStatus) {
            for (const item of systemStatus) {
                const message = printStatus(item.status);
                this.log(`${(item.system + ':').padEnd(11)}${message}`);
            }
        }
        else {
            core_1.ux.error(errorMessage, { exit: 1 });
        }
        if (herokuStatus) {
            for (const incident of herokuStatus.incidents) {
                core_1.ux.log();
                heroku_cli_util_1.hux.styledHeader(`${incident.title} ${color_1.default.yellow(incident.created_at)} ${color_1.default.cyan(incident.full_url)}`);
                const padding = (0, util_2.getMaxUpdateTypeLength)(incident.updates.map(update => update.update_type));
                for (const u of incident.updates) {
                    core_1.ux.log(`${color_1.default.yellow(u.update_type.padEnd(padding))} ${new Date(u.updated_at).toISOString()} (${(0, date_fns_1.formatDistanceToNow)(new Date(u.updated_at))} ago)`);
                    core_1.ux.log(`${u.contents}\n`);
                }
            }
        }
        else if (formattedTrustStatus) {
            for (const incident of formattedTrustStatus.incidents) {
                core_1.ux.log();
                heroku_cli_util_1.hux.styledHeader(`${incident.id} ${color_1.default.yellow(incident.createdAt)} ${color_1.default.cyan(`https://status.salesforce.com/incidents/${incident.id}`)}`);
                const padding = (0, util_2.getMaxUpdateTypeLength)(incident.IncidentEvents.map(event => { var _a; return (_a = event.localizedType) !== null && _a !== void 0 ? _a : event.type; }));
                for (const event of incident.IncidentEvents) {
                    const eventType = (_a = event.localizedType) !== null && _a !== void 0 ? _a : event.type;
                    core_1.ux.log(`${color_1.default.yellow(eventType.padEnd(padding))} ${new Date(event.createdAt).toISOString()} (${(0, date_fns_1.formatDistanceToNow)(new Date(event.createdAt))} ago)`);
                    core_1.ux.log(`${event.message}\n`);
                }
            }
        }
    }
}
exports.default = Status;
Status.description = 'display current status of the Heroku platform';
Status.flags = {
    json: core_1.Flags.boolean({ description: 'output in json format' }),
};

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.displayHostsAsJSON = exports.displayHosts = void 0;
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const format_1 = require("./format");
function displayHosts(space, hosts) {
    heroku_cli_util_1.hux.styledHeader(`${space} Hosts`);
    heroku_cli_util_1.hux.table(hosts, {
        host_id: {
            header: 'Host ID',
        },
        state: {
            header: 'State',
            get: host => (0, format_1.hostStatus)(host.state),
        },
        available_capacity_percentage: {
            header: 'Available Capacity',
            get: host => `${host.available_capacity_percentage}%`,
        },
        allocated_at: {
            header: 'Allocated At',
            get: host => host.allocated_at || '',
        },
        released_at: {
            header: 'Released At',
            get: host => host.released_at || '',
        },
    });
}
exports.displayHosts = displayHosts;
function displayHostsAsJSON(hosts) {
    core_1.ux.log(JSON.stringify(hosts, null, 2));
}
exports.displayHostsAsJSON = displayHostsAsJSON;

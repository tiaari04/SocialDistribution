"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const tsheredoc_1 = require("tsheredoc");
const setter_1 = require("../../../lib/pg/setter");
const nls_1 = require("../../../nls");
class DataConnectorDetailsLogs extends setter_1.PGSettingsCommand {
    constructor() {
        super(...arguments);
        this.settingKey = 'data_connector_details_logs';
    }
    convertValue(val) {
        return (0, setter_1.booleanConverter)(val);
    }
    explain(setting) {
        if (setting === null || setting === void 0 ? void 0 : setting.value) {
            return 'Data replication slot details will be logged.';
        }
        return 'Data replication slot details will no longer be logged.';
    }
}
exports.default = DataConnectorDetailsLogs;
DataConnectorDetailsLogs.aliases = ['pg:settings:explain-data-connector-details'];
DataConnectorDetailsLogs.description = (0, tsheredoc_1.default)(`
  displays stats on replication slots on your database, the default value is "off"
  `);
DataConnectorDetailsLogs.flags = {
    app: command_1.flags.app({ required: true }),
    remote: command_1.flags.remote(),
};
DataConnectorDetailsLogs.args = {
    database: core_1.Args.string({ description: `${(0, nls_1.nls)('pg:database:arg:description')} ${(0, nls_1.nls)('pg:database:arg:description:default:suffix')}` }),
    value: core_1.Args.string({ description: 'boolean indicating if data replication slot details get logged' }),
};

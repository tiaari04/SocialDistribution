"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.displayTelemetryDrain = exports.validateAndFormatSignals = void 0;
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
function validateAndFormatSignals(signalInput) {
    const signalOptions = ['traces', 'metrics', 'logs'];
    if (!signalInput || signalInput === 'all')
        return signalOptions;
    const signalArray = signalInput.split(',');
    signalArray.forEach(signal => {
        if (!signalOptions.includes(signal)) {
            core_1.ux.error(`Invalid signal option: ${signalArray}. Run heroku telemetry:add --help to see signal options.`, { exit: 1 });
        }
    });
    return signalArray;
}
exports.validateAndFormatSignals = validateAndFormatSignals;
async function displayTelemetryDrain(telemetryDrain, heroku) {
    heroku_cli_util_1.hux.styledHeader(telemetryDrain.id);
    const displayObject = {
        Signals: telemetryDrain.signals.join(', '),
        Endpoint: telemetryDrain.exporter.endpoint,
        Transport: (telemetryDrain.exporter.type === 'otlp' ? 'gRPC' : 'HTTP'),
    };
    if (telemetryDrain.owner.type === 'space') {
        const { body: space } = await heroku.get(`/spaces/${telemetryDrain.owner.id}`, {
            headers: {
                Accept: 'application/vnd.heroku+json; version=3.sdk',
            },
        });
        displayObject.Space = space.name;
    }
    else {
        const { body: app } = await heroku.get(`/apps/${telemetryDrain.owner.id}`, {
            headers: {
                Accept: 'application/vnd.heroku+json; version=3.sdk',
            },
        });
        displayObject.App = app.name;
    }
    if (telemetryDrain.exporter.headers) {
        displayObject.Headers = JSON.stringify(telemetryDrain.exporter.headers);
    }
    heroku_cli_util_1.hux.styledObject(displayObject, ['App', 'Space', 'Signals', 'Endpoint', 'Transport', 'Headers']);
}
exports.displayTelemetryDrain = displayTelemetryDrain;

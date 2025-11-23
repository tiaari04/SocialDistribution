"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sendToHoneycomb = exports.sendTelemetry = exports.reportCmdNotFound = exports.computeDuration = exports.setupTelemetry = exports.initializeInstrumentation = exports.processor = void 0;
const command_1 = require("@heroku-cli/command");
const core_1 = require("@oclif/core");
const api_1 = require("@opentelemetry/api");
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { BatchSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const path = require('path');
const { version } = require('../package.json');
const root = path.resolve(__dirname, '../package.json');
const isDev = process.env.IS_DEV_ENVIRONMENT === 'true';
const isTelemetryDisabled = process.env.DISABLE_TELEMETRY === 'true';
function getToken() {
    const config = new core_1.Config({ root });
    const heroku = new command_1.APIClient(config);
    return heroku.auth;
}
const debug = require('debug')('global_telemetry');
registerInstrumentations({
    instrumentations: [],
});
const resource = Resource
    .default()
    .merge(new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'heroku-cli',
    [SemanticResourceAttributes.SERVICE_VERSION]: version,
}));
const provider = new NodeTracerProvider({
    resource,
});
const headers = { Authorization: `Bearer ${process.env.IS_HEROKU_TEST_ENV !== 'true' ? getToken() : ''}` };
const exporter = new OTLPTraceExporter({
    url: isDev ? 'https://backboard.staging.herokudev.com/otel/v1/traces' : 'https://backboard.heroku.com/otel/v1/traces',
    headers,
    compression: 'none',
});
exports.processor = new BatchSpanProcessor(exporter);
provider.addSpanProcessor(exports.processor);
function initializeInstrumentation() {
    provider.register();
}
exports.initializeInstrumentation = initializeInstrumentation;
function setupTelemetry(config, opts) {
    const now = new Date();
    const cmdStartTime = now.getTime();
    const isRegularCmd = Boolean(opts.Command);
    const mcpMode = process.env.HEROKU_MCP_MODE === 'true';
    const mcpServerVersion = process.env.HEROKU_MCP_SERVER_VERSION || 'unknown';
    const irregularTelemetryObject = {
        command: opts.id,
        os: config.platform,
        version: `${config.version}${mcpMode ? ` (MCP ${mcpServerVersion})` : ''}`,
        exitCode: 0,
        exitState: 'successful',
        cliRunDuration: 0,
        commandRunDuration: cmdStartTime,
        lifecycleHookCompletion: {
            init: true,
            prerun: false,
            postrun: false,
            command_not_found: false,
        },
        isVersionOrHelp: true,
    };
    if (isRegularCmd) {
        return Object.assign(Object.assign({}, irregularTelemetryObject), { command: opts.Command.id, isVersionOrHelp: false, lifecycleHookCompletion: Object.assign(Object.assign({}, irregularTelemetryObject.lifecycleHookCompletion), { prerun: true }) });
    }
    return irregularTelemetryObject;
}
exports.setupTelemetry = setupTelemetry;
function computeDuration(cmdStartTime) {
    // calculate time duration from start time till now
    const now = new Date();
    const cmdFinishTime = now.getTime();
    return cmdFinishTime - cmdStartTime;
}
exports.computeDuration = computeDuration;
function reportCmdNotFound(config) {
    return {
        command: 'invalid_command',
        os: config.platform,
        version: config.version,
        exitCode: 0,
        exitState: 'command_not_found',
        cliRunDuration: 0,
        commandRunDuration: 0,
        lifecycleHookCompletion: {
            init: true,
            prerun: false,
            postrun: false,
            command_not_found: true,
        },
        isVersionOrHelp: false,
    };
}
exports.reportCmdNotFound = reportCmdNotFound;
async function sendTelemetry(currentTelemetry) {
    // send telemetry to honeycomb
    if (isTelemetryDisabled) {
        return;
    }
    const telemetry = currentTelemetry;
    await sendToHoneycomb(telemetry);
}
exports.sendTelemetry = sendTelemetry;
async function sendToHoneycomb(data) {
    try {
        const tracer = api_1.default.trace.getTracer('heroku-cli', version);
        const span = tracer.startSpan('node_app_execution');
        if (data instanceof Error) {
            span.recordException(data);
            span.setStatus({
                code: api_1.SpanStatusCode.ERROR,
                message: data.message,
            });
        }
        else {
            span.setAttribute('heroku_client.command', data.command);
            span.setAttribute('heroku_client.os', data.os);
            span.setAttribute('heroku_client.version', data.version);
            span.setAttribute('heroku_client.exit_code', data.exitCode);
            span.setAttribute('heroku_client.exit_state', data.exitState);
            span.setAttribute('heroku_client.cli_run_duration', data.cliRunDuration);
            span.setAttribute('heroku_client.command_run_duration', data.commandRunDuration);
            span.setAttribute('heroku_client.lifecycle_hook.init', data.lifecycleHookCompletion.init);
            span.setAttribute('heroku_client.lifecycle_hook.prerun', data.lifecycleHookCompletion.prerun);
            span.setAttribute('heroku_client.lifecycle_hook.postrun', data.lifecycleHookCompletion.postrun);
            span.setAttribute('heroku_client.lifecycle_hook.command_not_found', data.lifecycleHookCompletion.command_not_found);
        }
        span.end();
        exports.processor.forceFlush();
    }
    catch (_a) {
        debug('could not send telemetry');
    }
}
exports.sendToHoneycomb = sendToHoneycomb;

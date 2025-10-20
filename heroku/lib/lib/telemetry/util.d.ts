import { TelemetryDrain } from '../types/telemetry';
import { APIClient } from '@heroku-cli/command';
export declare function validateAndFormatSignals(signalInput: string | undefined): string[];
export declare function displayTelemetryDrain(telemetryDrain: TelemetryDrain, heroku: APIClient): Promise<void>;

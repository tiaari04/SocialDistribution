import { ConnectionDetails } from '@heroku/heroku-cli-util';
import { ChildProcess } from 'node:child_process';
export declare const parseExclusions: (rawExcludeList: string | undefined) => string[];
export declare const prepare: (target: ConnectionDetails) => Promise<void>;
export declare const maybeTunnel: (herokuDb: ConnectionDetails) => Promise<ConnectionDetails>;
export declare const connArgs: (uri: ConnectionDetails, skipDFlag?: boolean) => string[];
export declare const spawnPipe: (pgDump: ChildProcess, pgRestore: ChildProcess) => Promise<void>;
export declare const verifyExtensionsMatch: (source: ConnectionDetails, target: ConnectionDetails) => Promise<void>;

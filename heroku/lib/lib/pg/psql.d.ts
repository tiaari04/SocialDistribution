/// <reference types="node" />
/// <reference types="node" />
import { SpawnOptions } from 'child_process';
import { ConnectionDetailsWithAttachment } from '@heroku/heroku-cli-util';
export declare function fetchVersion(db: ConnectionDetailsWithAttachment): Promise<string | undefined>;
export declare function psqlFileOptions(file: string, dbEnv: NodeJS.ProcessEnv): {
    dbEnv: NodeJS.ProcessEnv;
    psqlArgs: string[];
    childProcessOptions: SpawnOptions;
};
export declare function psqlInteractiveOptions(prompt: string, dbEnv: NodeJS.ProcessEnv): {
    dbEnv: NodeJS.ProcessEnv;
    psqlArgs: string[];
    childProcessOptions: SpawnOptions;
};
export declare function execFile(db: ConnectionDetailsWithAttachment, file: string): Promise<string>;
export declare function interactive(db: ConnectionDetailsWithAttachment): Promise<string>;

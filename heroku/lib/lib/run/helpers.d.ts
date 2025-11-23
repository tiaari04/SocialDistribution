import type { APIClient } from '@heroku-cli/command';
export declare function revertSortedArgs(processArgs: Array<string>, argv: Array<string>): string[];
export declare function buildCommand(args: Array<string>, prependLauncher?: boolean): string;
export declare function buildEnvFromFlag(flag: string): {};
/**
 * Determines whether to prepend `launcher` to the command for a given app.
 * Behavior: Only prepend on CNB stack apps and when not explicitly disabled.
 */
export declare function shouldPrependLauncher(heroku: APIClient, appName: string, disableLauncher: boolean): Promise<boolean>;
/**
 * Builds the command string, automatically deciding whether to prepend `launcher`.
 */
export declare function buildCommandWithLauncher(heroku: APIClient, appName: string, args: string[], disableLauncher: boolean): Promise<string>;

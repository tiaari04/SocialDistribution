import { APIClient } from '@heroku-cli/command';
import * as Heroku from '@heroku-cli/schema';
import { ExtendedAddonAttachment } from '@heroku/heroku-cli-util';
export declare function arbitraryAppDB(heroku: APIClient, app: string): Promise<Heroku.AddOn>;
export declare function all(heroku: APIClient, app_id: string): Promise<Array<ExtendedAddonAttachment['addon'] & {
    attachment_names?: string[];
}>>;
export declare function getRelease(heroku: APIClient, appName: string, id: string): Promise<Heroku.Release>;

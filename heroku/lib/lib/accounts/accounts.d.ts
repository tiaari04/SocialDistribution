import * as Heroku from '@heroku-cli/schema';
export declare function list(): Heroku.Account[] | [];
export declare function current(): string | null;
export declare function add(name: string, username: string, password: string): void;
export declare function remove(name: string): void;
export declare function set(name: string): void;

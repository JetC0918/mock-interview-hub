/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type User = {
    id?: string;
    username?: string;
    email?: string;
    avatar?: string;
    role?: User.role;
    createdAt?: string;
};
export namespace User {
    export enum role {
        HOST = 'host',
        PARTICIPANT = 'participant',
        SPECTATOR = 'spectator',
    }
}


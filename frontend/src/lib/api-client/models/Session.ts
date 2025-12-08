/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Participant } from './Participant';
import type { Problem } from './Problem';
import type { SupportedLanguage } from './SupportedLanguage';
export type Session = {
    id?: string;
    pin?: string;
    hostId?: string;
    title?: string;
    description?: string;
    language?: SupportedLanguage;
    participants?: Array<Participant>;
    code?: string;
    status?: Session.status;
    createdAt?: string;
    problem?: Problem;
};
export namespace Session {
    export enum status {
        WAITING = 'waiting',
        ACTIVE = 'active',
        ENDED = 'ended',
    }
}


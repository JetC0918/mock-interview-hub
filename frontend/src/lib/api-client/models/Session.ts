/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Participant } from './Participant';
import type { Problem } from './Problem';
import type { SessionStatus } from './SessionStatus';
import type { SupportedLanguage } from './SupportedLanguage';
export type Session = {
    code?: string;
    codeRevision: number;
    createdAt: string;
    description?: (string | null);
    hostId: string;
    id: string;
    language: SupportedLanguage;
    participants?: Array<Participant>;
    pin: string;
    problem?: (Problem | null);
    status: SessionStatus;
    title: string;
};


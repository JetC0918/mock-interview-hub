/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Problem } from './Problem';
import type { PublicParticipant } from './PublicParticipant';
import type { SessionStatus } from './SessionStatus';
import type { SupportedLanguage } from './SupportedLanguage';
/**
 * Restricted session projection for unauthenticated direct-link viewing.
 */
export type PublicSession = {
    code?: string;
    codeRevision: number;
    createdAt: string;
    description?: (string | null);
    id: string;
    language: SupportedLanguage;
    participants?: Array<PublicParticipant>;
    problem?: (Problem | null);
    status: SessionStatus;
    title: string;
};


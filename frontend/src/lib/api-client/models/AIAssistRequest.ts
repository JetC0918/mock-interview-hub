/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProblemContext } from './ProblemContext';
/**
 * Request model for AI assistance.
 */
export type AIAssistRequest = {
    message: string;
    problemContext?: (ProblemContext | null);
    requestId: string;
    sessionId: string;
};


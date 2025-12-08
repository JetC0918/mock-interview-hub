/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecutionResult } from '../models/ExecutionResult';
import type { Problem } from '../models/Problem';
import type { SupportedLanguage } from '../models/SupportedLanguage';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ExecutionService {
    /**
     * Run code
     * @param requestBody
     * @returns ExecutionResult Execution result
     * @throws ApiError
     */
    public static postExecutionRun(
        requestBody: {
            code: string;
            language: SupportedLanguage;
        },
    ): CancelablePromise<ExecutionResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/execution/run',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Run tests
     * @param requestBody
     * @returns ExecutionResult Test execution result
     * @throws ApiError
     */
    public static postExecutionTest(
        requestBody: {
            code: string;
            language: SupportedLanguage;
            problem: Problem;
        },
    ): CancelablePromise<ExecutionResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/execution/test',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
}

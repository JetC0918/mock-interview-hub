/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecutionRequest } from '../models/ExecutionRequest';
import type { ExecutionResult } from '../models/ExecutionResult';
import type { TestRequest } from '../models/TestRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ExecutionService {
    /** Legacy aliases retained while callers migrate to descriptive names. */
    public static postExecutionRun(requestBody: import('../models/ExecutionRequest').ExecutionRequest): CancelablePromise<import('../models/ExecutionResult').ExecutionResult> {
        return this.runCodeExecutionRunPost({ requestBody });
    }
    public static postExecutionTest(requestBody: import('../models/TestRequest').TestRequest): CancelablePromise<import('../models/ExecutionResult').ExecutionResult> {
        return this.runTestsExecutionTestPost({ requestBody });
    }
    /**
     * Run Code
     * Code execution is disabled on the server for security reasons.
     * Please use the browser-based code execution (WebAssembly).
     * @returns ExecutionResult Successful Response
     * @throws ApiError
     */
    public static runCodeExecutionRunPost({
        requestBody,
    }: {
        requestBody: ExecutionRequest,
    }): CancelablePromise<ExecutionResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/execution/run',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Run Tests
     * Test execution is disabled on the server for security reasons.
     * Please use the browser-based test execution (WebAssembly).
     * @returns ExecutionResult Successful Response
     * @throws ApiError
     */
    public static runTestsExecutionTestPost({
        requestBody,
    }: {
        requestBody: TestRequest,
    }): CancelablePromise<ExecutionResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/execution/test',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
